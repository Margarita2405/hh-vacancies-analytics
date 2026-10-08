from typing import Any, Dict, List, Optional, Tuple, cast

import psycopg2

from src.config import DB_CONFIG


class DBManager:
    """Класс для работы с БД PostgreSQL. Отвечает за вставку данных о работодателях и вакансиях,
    а также за выполнение аналитических запросов к базе."""

    def __init__(self) -> None:
        """Инициализирует соединение с базой данных при создании объекта.
        Параметры подключения берутся из конфигурационного модуля config.py."""
        # Устанавливаем соединение с БД, распаковывая словарь DB_CONFIG
        self.conn = psycopg2.connect(**DB_CONFIG)  # type: ignore[call-overload]

    def insert_employer(self, employer_data: Dict[str, Any]) -> None:
        """Добавляет информацию о работодателе в таблицу employers ('id', 'name', 'url', 'description').
        Если работодатель с таким employer_id уже существует, запись игнорируется."""
        # Используем курсор для выполнения SQL-запроса
        with self.conn.cursor() as cur:
            # SQL-запрос вставки с защитой от конфликта по первичному ключу
            cur.execute(
                """
                INSERT INTO employers (employer_id, name, url, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (employer_id) DO NOTHING
            """,
                (
                    employer_data["id"],  # обязательный ключ
                    employer_data["name"],  # обязательный ключ
                    employer_data.get("url"),  # может отсутствовать → None
                    employer_data.get("description"),  # может отсутствовать → None
                ),
            )
        # Фиксируем изменения в БД (делаем COMMIT)
        self.conn.commit()

    def insert_vacancy(self, vacancy_data: Dict[str, Any], employer_id: int) -> None:
        """Добавляет информацию о вакансии в таблицу vacancies.
        Если вакансия с таким vacancy_id уже существует, запись игнорируется.
        Поле salary в ответе API может отсутствовать, поэтому обрабатываем его аккуратно."""
        # Извлекаем информацию о зарплате (может быть None)
        salary = vacancy_data.get("salary")
        # Если зарплата указана, берём её границы и валюту, иначе None
        salary_from = salary["from"] if salary else None
        salary_to = salary["to"] if salary else None
        currency = salary["currency"] if salary else None

        # Используем курсор для выполнения SQL-запроса
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO vacancies (vacancy_id, employer_id, name, salary_from, salary_to, currency, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (vacancy_id) DO NOTHING
            """,
                (
                    vacancy_data["id"],  # ID вакансии
                    employer_id,  # ID работодателя (связь)
                    vacancy_data["name"],  # Название вакансии
                    salary_from,  # Нижняя граница ЗП или NULL
                    salary_to,  # Верхняя граница ЗП или NULL
                    currency,  # Валюта или NULL
                    vacancy_data["alternate_url"],  # Прямая ссылка на вакансию на hh.ru
                ),
            )
        # Фиксируем изменения в БД (делаем COMMIT)
        self.conn.commit()

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """Получает список всех компаний и количество вакансий, опубликованных каждой компанией.
        Возвращает список кортежей (название_компании, количество_вакансий)."""
        # Используем курсор для выполнения SQL-запроса
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.name, COUNT(v.vacancy_id)
                FROM employers e
                LEFT JOIN vacancies v ON e.employer_id = v.employer_id
                GROUP BY e.employer_id
            """)
            # fetchall() возвращает список кортежей, например: [('Яндекс', 15), ('Сбер', 8), ...]
            return cast(List[Tuple[str, int]], cur.fetchall())

    def get_all_vacancies(self) -> List[Tuple[str, str, Optional[int], Optional[int], Optional[str], str]]:
        """Получает список всех вакансий с подробной информацией:
        название компании, название вакансии, зарплата (от, до), валюта, ссылка на вакансию.
        Возвращает список кортежей."""
        # Используем курсор для выполнения SQL-запроса
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.name, v.name, v.salary_from, v.salary_to, v.currency, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
            """)
            # fetchall() возвращает список кортежей
            return cast(List[Tuple[str, str, Optional[int], Optional[int], Optional[str], str]], cur.fetchall())

    def get_avg_salary(self) -> float:
        """Вычисляет среднюю зарплату по всем вакансиям.
        Для каждой вакансии берётся среднее арифметическое между salary_from и salary_to,
        затем вычисляется общее среднее.
        Вакансии, у которых не указана ни одна граница зарплаты, игнорируются.
        Возвращает среднюю зарплату (float). Если подходящих вакансий нет, возвращается 0.0."""
        # Используем курсор для выполнения SQL-запроса
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT AVG((COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2.0)
                FROM vacancies
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
            """)
            # fetchone() возвращает кортеж из одного элемента, берём первый
            result = cur.fetchone()[0]
            # Если результат None (нет вакансий с зарплатой), возвращаем 0.0
            return float(result) if result is not None else 0.0

    def get_vacancies_with_higher_salary(
        self,
    ) -> List[Tuple[str, str, Optional[int], Optional[int], Optional[str], str]]:
        """Возвращает список вакансий, у которых средняя зарплата (от+до)/2 выше средней зарплаты
        по всем вакансиям. Возвращает список вакансий (аналогично get_all_vacancies), отфильтрованный
        по условию."""
        # Сначала получаем среднюю зарплату по всем вакансиям
        avg = self.get_avg_salary()

        # Используем курсор для выполнения SQL-запроса
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.name, v.name, v.salary_from, v.salary_to, v.currency, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE (COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2.0 > %s
            """,
                (avg,),
            )
            # Возвращаем список вакансий
            return cast(List[Tuple[str, str, Optional[int], Optional[int], Optional[str], str]], cur.fetchall())

    def get_vacancies_with_keyword(
        self, keyword: str
    ) -> List[Tuple[str, str, Optional[int], Optional[int], Optional[str], str]]:
        """Возвращает список вакансий, в названии которых содержится заданное ключевое слово, например, "python"
        (без учёта регистра). Возвращает список вакансий, удовлетворяющих условию."""
        # Используем курсор для выполнения SQL-запроса
        with self.conn.cursor() as cur:
            # Оператор ILIKE выполняет поиск без учёта регистра, % – любое количество символов
            cur.execute(
                """
                SELECT e.name, v.name, v.salary_from, v.salary_to, v.currency, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                WHERE v.name ILIKE %s
            """,
                (f"%{keyword}%",),
            )
            # Возвращает список вакансий
            return cast(List[Tuple[str, str, Optional[int], Optional[int], Optional[str], str]], cur.fetchall())

    def close(self) -> None:
        """Закрывает соединение с базой данных. Рекомендуется вызывать при завершении работы."""
        self.conn.close()
