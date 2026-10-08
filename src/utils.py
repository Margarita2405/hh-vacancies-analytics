import psycopg2

from src.config import DB_CONFIG


def create_database() -> None:
    """Создаёт базу данных PostgreSQL, если она не существует. Подключается к стандартной системной
    базе данных 'postgres', проверяет наличие целевой БД и создаёт её при отсутствии."""
    # Подключаемся к стандартной БД 'postgres', чтобы создать новую
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database="postgres",
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )

    # Включаем режим автокоммита — каждое выполнение SQL сразу фиксируется.
    conn.autocommit = True

    # Создаём курсор для выполнения SQL-запросов
    cur = conn.cursor()

    # Проверяем, существует ли уже база данных с именем из конфигурации
    # pg_database — системная таблица со списком всех БД в кластере PostgreSQL
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_CONFIG['database']}'")

    # Если запрос вернул пустой результат (fetchone() == None), базы данных нет
    if not cur.fetchone():
        # Создаём новую базу данных
        cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        print(f"База данных '{DB_CONFIG['database']}' успешно создана.")
    else:
        print(f"База данных '{DB_CONFIG['database']}' уже существует.")

    # Закрываем курсор и соединение, чтобы освободить ресурсы
    cur.close()
    conn.close()


def create_tables() -> None:
    """Создаёт таблицы employers и vacancies в целевой базе данных.
    Если таблицы уже существуют, ничего не пересоздаётся (благодаря IF NOT EXISTS).
    Устанавливается связь внешнего ключа между вакансиями и работодателями."""
    # Подключаемся к целевой базе данных (имя берётся из DB_CONFIG)
    # Конструкция with автоматически закроет соединение и курсор при выходе из блока
    with psycopg2.connect(**DB_CONFIG) as conn:  # type: ignore[call-overload]
        # Создаём курсор внутри контекстного менеджера — он закроется автоматически
        with conn.cursor() as cur:
            # Выполняем SQL-скрипт для создания таблиц
            cur.execute("""
                -- Таблица работодателей
                CREATE TABLE IF NOT EXISTS employers (
                    employer_id INT PRIMARY KEY,        -- Уникальный ID работодателя с hh.ru
                    name VARCHAR(255) NOT NULL,         -- Название компании
                    url VARCHAR(255),                   -- Ссылка на страницу компании на hh.ru
                    description TEXT                    -- Описание компании
                );
                -- Таблица вакансий
                CREATE TABLE IF NOT EXISTS vacancies (
                    vacancy_id INT PRIMARY KEY,         -- Уникальный ID вакансии с hh.ru
                    employer_id INT REFERENCES employers(employer_id) ON DELETE CASCADE,
                            -- Внешний ключ: каждая вакансия привязана к работодателю
                            -- ON DELETE CASCADE означает: при удалении работодателя удаляются все его вакансии
                    name VARCHAR(255) NOT NULL,        -- Название вакансии
                    salary_from INT,                   -- Нижняя граница зарплаты (может быть NULL)
                    salary_to INT,                     -- Верхняя граница зарплаты (может быть NULL)
                    currency VARCHAR(3),               -- Валюта (RUB, USD и т.д.)
                    url VARCHAR(255)                   -- Прямая ссылка на вакансию на hh.ru
                );
            """)
            print("Таблицы 'employers' и 'vacancies' созданы (или уже существовали).")
