# Проект: Поиск вакансий с hh.ru (анализ данных в PostgreSQL)

## Описание проекта

Данный проект представляет собой консольное приложение на Python, которое:
- Получает данные о работодателях и их вакансиях с публичного API hh.ru.
- Сохраняет полученные данные в базу данных PostgreSQL.
- Предоставляет пользователю интерактивный интерфейс для аналитики: список компаний с количеством вакансий, все вакансии, средняя зарплата, вакансии с зарплатой выше средней, поиск по ключевым словам.

## Технологии

- Python 3.13
- PostgreSQL (база данных)
- psycopg2 — драйвер для работы с PostgreSQL
- requests — для запросов к API hh.ru
- python-dotenv — для управления переменными окружения
- poetry — управление зависимостями и окружением
- pytest — тестирование проекта
- mypy, flake8, isort, black — статическая типизация, линтинг и форматирование

## Структура проекта

```text
hh-vacancies-analytics/
├── src/
│   ├── __init__.py
│   ├── api_client.py      # Взаимодействие с API hh.ru
│   ├── config.py          # Загрузка конфигурации из .env
│   ├── db_manager.py      # Класс DBManager (запись и чтение БД)
│   └── utils.py           # Создание БД и таблиц
├── tests/                 # Модульные тесты (pytest)
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_db_manager.py
│   └── test_utils.py
├── .env                   # Переменные окружения (не попадает в репозиторий)
├── .env.example           # Пример файла .env
├── .flake8                # Конфигурационный файл flake8
├── .gitignore             # Игнорируемые файлы
├── main.py                # Точка входа, пользовательское меню
├── pyproject.toml         # Зависимости и настройки проекта Poetry
└── README.md              # Описание проекта
```

## Документация классов и модулей

### `class HHAPIClient`
Класс для работы с публичным API hh.ru.
* **get_employer(employer_id: int)** — Получить информацию о работодателе по ID.
* **get_vacancies(employer_id: int, per_page: int = 100)** — Получить список вакансий для указанного работодателя.

### `class DBManager`
Класс для работы с БД PostgreSQL. Отвечает за вставку данных и выполнение аналитических запросов.
* **insert_employer(employer_data: dict)** — Добавляет информацию о работодателе в таблицу `employers`.
* **insert_vacancy(vacancy_data: dict, employer_id: int)** — Добавляет информацию о вакансии в таблицу `vacancies`.
* **get_companies_and_vacancies_count()** — Получает список всех компаний и количество вакансий у каждой.
* **get_all_vacancies()** — Получает список всех вакансий с подробной информацией.
* **get_avg_salary()** — Вычисляет среднюю зарплату по всем сохраненным вакансиям.
* **get_vacancies_with_higher_salary()** — Возвращает список вакансий, зарплата которых выше средней.
* **get_vacancies_with_keyword(keyword: str)** — Возвращает список вакансий, содержащих в названии ключевое слово.

### Модуль `utils.py`
* **create_database()** — Автоматически создаёт базу данных PostgreSQL, если она не существует.
* **create_tables()** — Создаёт таблицы `employers` и `vacancies` со связями Foreign Key.

## Схема базы данных 

```sql
CREATE TABLE employers (
    employer_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(255),
    description TEXT
);

CREATE TABLE vacancies (
    vacancy_id INT PRIMARY KEY,
    employer_id INT REFERENCES employers(employer_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    salary_from INT,
    salary_to INT,
    currency VARCHAR(3),
    url VARCHAR(255)
);
```

## Установка и запуск

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/Margarita2405/hh-vacancies-analytics
cd hh-vacancies-analytics
```

### 2. Настройте виртуальное окружение и установите зависимости через Poetry
```bash
poetry install
```

### 3. Настройте подключение к PostgreSQL
Создайте файл `.env` в корне проекта на основе примера из `.env.example`:
```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hh_parser
DB_USER=postgres
DB_PASSWORD=ваш_собственный_пароль
```

### 4. Запустите приложение
```bash
poetry run python main.py
```
*При первом запуске программа автоматически создаст базу данных, необходимые таблицы, а затем наполнит их актуальными данными с hh.ru.*

## Использование

После запуска приложения появится интерактивное текстовое меню:
1. Список компаний и количество вакансий
2. Список всех вакансий
3. Средняя зарплата по всем вакансиям
4. Вакансии с зарплатой выше средней
5. Поиск вакансий по ключевому слову
0. Выход

### Примеры вывода данных

<details>
<summary>Список компаний и количество вакансий</summary>

```text
Яндекс: 15 вакансий
Сбер: 8 вакансий
Тинькофф: 22 вакансии
```
</details>

<details>
<summary>Поиск по ключевому слову "python"</summary>

```text
Яндекс | Senior Python Developer | ЗП: 250000 - 350000 RUB | https://hh.ru/vacancy/123456
Альфа-Банк | Python-разработчик (удаленно) | Зарплата не указана | https://hh.ru/vacancy/789012
```
</details>

## Тестирование и линтинг

### Запуск модульных тестов (Pytest)
Все критически важные функции проекта (работа с API, методы менеджера БД, функции утилит) полностью покрыты модульными тестами с использованием моков. Для запуска тестов выполните:
```bash
pytest tests
```

### Запуск статического анализа и линтеров
Для проверки качества кода, соответствия стандартам PEP 8 и правильности типов запустите команды:
```bash
black src/main.py
isort src/main.py
flake8 src/main.py
mypy src/main.py
```

## 👩‍💻 Автор

**Маргарита Буршева**
- **Email:** mbursheva@mail.ru
- **GitHub:** [hh-vacancies-analytics](https://github.com/Margarita2405)

*Курсовой проект выполнен в рамках программы бэкенд-обучения Университета Skypro.*