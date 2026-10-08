from src.api_client import HHAPIClient
from src.db_manager import DBManager
from src.utils import create_database, create_tables


def main() -> None:
    """Главная функция приложения. Последовательно выполняет все шаги проекта:
    - подготовка БД,
    - наполнение данными (только при первом запуске),
    - диалог с пользователем."""

    # ШАГ 1. ПОДГОТОВКА БАЗЫ ДАННЫХ
    # Создаем базу данных PostgreSQL, если она ещё не существует.
    # Функция create_database() подключается к служебной БД 'postgres',
    # проверяет наличие целевой БД (имя из DB_CONFIG) и создаёт её при отсутствии.
    create_database()

    # Создаём таблицы 'employers' и 'vacancies' внутри целевой БД.
    # Если таблицы уже есть, ничего не пересоздаётся (благодаря IF NOT EXISTS).
    # Устанавливается связь внешнего ключа между вакансиями и работодателями.
    create_tables()

    # ШАГ 2. ЗАГРУЗКА ДАННЫХ ИЗ API
    # Создаём экземпляр DBManager – он сразу подключается к БД.
    db = DBManager()

    # Создаём экземпляр клиента для работы с API hh.ru.
    # Внутри init заданы base_url и заголовки User-Agent.
    api = HHAPIClient()

    # Список ID работодателей на hh.ru (не менее 10).
    # ID можно найти в URL карточки компании на hh.ru: https://hh.ru/employer/1740
    employer_ids = [
        1740,  # Яндекс
        3529,  # Сбер
        78638,  # Тинькофф
        2180,  # Ozon
        15478,  # VK
        80,  # МТС
        3776,  # Газпромбанк
        1057,  # Ростелеком
        87021,  # Wildberries
        39305,  # Авито
    ]

    # Проверяем, загружены ли уже данные в таблицу employers.
    # Если таблица пуста – выполняем загрузку. Это предотвращает повторную загрузку
    # при каждом запуске программы, экономя время и запросы к API.
    with db.conn.cursor() as cur:
        # Подсчитываем количество записей в таблице employers
        cur.execute("SELECT COUNT(*) FROM employers")
        # fetchone() возвращает кортеж, берём первый элемент
        count = cur.fetchone()[0]

        # Если записей нет (count == 0), загружаем данные
        if count == 0:
            print("База данных пуста. Начинаю загрузку данных с hh.ru...")

            # Перебираем всех работодателей из списка
            for eid in employer_ids:
                print(f"  Загружаю компанию с ID {eid}...")

                # Получаем данные о работодателе (словарь от API)
                employer = api.get_employer(eid)
                # Сохраняем работодателя в таблицу employers
                db.insert_employer(employer)

                # Получаем список вакансий этого работодателя (до 100 на страницу, все страницы)
                vacancies = api.get_vacancies(eid)
                print(f"    Найдено вакансий: {len(vacancies)}")

                # Сохраняем каждую вакансию в таблицу vacancies,
                # передавая employer_id для связи с таблицей employers
                for vac in vacancies:
                    db.insert_vacancy(vac, eid)

            print("Загрузка данных завершена.\n")
        else:
            # Если данные уже есть, просто сообщаем об этом и продолжаем работу.
            print(f"В базе данных уже есть {count} компаний. Загрузка не требуется.\n")

    # ШАГ 3. ИНТЕРАКТИВНОЕ МЕНЮ ПОЛЬЗОВАТЕЛЯ
    # Бесконечный цикл, который прерывается только при выборе пункта "0"
    while True:
        # Выводим красивое меню с вариантами действий
        print("\n" + "=" * 50)
        print("Добро пожаловать в анализатор вакансий с hh.ru!")
        print("Выберите действие:")
        print("1. Список компаний и количество их вакансий")
        print("2. Список всех вакансий (компания, название, зарплата, ссылка)")
        print("3. Средняя зарплата по всем вакансиям")
        print("4. Вакансии с зарплатой выше средней")
        print("5. Поиск вакансий по ключевому слову в названии")
        print("0. Выход")
        print("=" * 50)

        # Запрашиваем ввод пользователя
        choice = input("Ваш выбор: ").strip()

        # Пункт 1: Компании и количество вакансий
        if choice == "1":
            # Метод DBManager возвращает список кортежей (название_компании, количество_вакансий)
            companies_count = db.get_companies_and_vacancies_count()
            print("\n--- Компании и количество вакансий ---")
            for name, count in companies_count:
                print(f"{name}: {count} вакансий")

        # Пункт 2: Все вакансии (подробно)
        elif choice == "2":
            all_vacancies = db.get_all_vacancies()
            print("\n--- Список всех вакансий ---")
            # Каждый кортеж: (компания, вакансия, зп_от, зп_до, валюта, ссылка)
            for rec in all_vacancies:
                company, vacancy, sal_from, sal_to, currency, url = rec
                # Формируем строку зарплаты: если оба значения None, пишем "не указана"
                if sal_from is None and sal_to is None:
                    salary_str = "Зарплата не указана"
                else:
                    salary_str = f"ЗП: {sal_from or '?'} - {sal_to or '?'} {currency or ''}"
                print(f"{company} | {vacancy} | {salary_str} | {url}")

        # Пункт 3: Средняя зарплата
        elif choice == "3":
            avg = db.get_avg_salary()
            # Выводим с двумя знаками после запятой
            print(f"\n--- Средняя зарплата по всем вакансиям ---\n{avg:.2f}")

        # Пункт 4: Вакансии с зарплатой выше средней
        elif choice == "4":
            higher_salary_vacancies = db.get_vacancies_with_higher_salary()
            print("\n--- Вакансии с зарплатой выше средней ---")
            if not higher_salary_vacancies:
                print("Нет вакансий с зарплатой выше средней.")
            for rec in higher_salary_vacancies:
                company, vacancy, sal_from, sal_to, currency, url = rec
                salary_str = f"ЗП: {sal_from or '?'} - {sal_to or '?'} {currency or ''}"
                print(f"{company} | {vacancy} | {salary_str} | {url}")

        # Пункт 5: Поиск по ключевому слову
        elif choice == "5":
            keyword = input("Введите ключевое слово для поиска (например, 'python'): ").strip()
            if not keyword:
                print("Ключевое слово не может быть пустым.")
                continue  # возвращаемся в начало цикла, не выполняя поиск
            keyword_vacancies = db.get_vacancies_with_keyword(keyword)
            print(f"\n--- Вакансии, содержащие '{keyword}' в названии ---")
            if not keyword_vacancies:
                print("Ничего не найдено.")
            for rec in keyword_vacancies:
                company, vacancy, sal_from, sal_to, currency, url = rec
                salary_str = f"ЗП: {sal_from or '?'} - {sal_to or '?'} {currency or ''}"
                print(f"{company} | {vacancy} | {salary_str} | {url}")

        # Пункт 0: Выход из программы
        elif choice == "0":
            print("Выход из программы. До свидания!")
            break  # прерываем бесконечный цикл while

        # Обработка неверного ввода
        else:
            print("Неверный выбор. Пожалуйста, введите число от 0 до 5.")
    # ЗАВЕРШЕНИЕ РАБОТЫ
    # Закрываем соединение с базой данных, чтобы освободить ресурсы.
    db.close()
    print("Ресурсы БД освобождены.")


# Точка входа в скрипт: если файл запущен напрямую (а не импортирован как модуль),
# то вызывается функция main().
if __name__ == "__main__":
    main()
