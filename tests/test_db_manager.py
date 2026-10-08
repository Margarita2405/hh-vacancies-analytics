from unittest.mock import MagicMock

import pytest

from src.db_manager import DBManager


@pytest.fixture
def mock_db_manager():
    """Создает экземпляр DBManager с правильной подменой контекстного менеджера курсора."""
    manager = DBManager()
    manager.conn = MagicMock()

    # Имитируем поведение конструкции: with conn.cursor() as cur:
    mock_cursor = MagicMock()
    manager.conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Сохраняем ссылку на мок-курсор внутри фикстуры для настройки ответов
    manager._test_cursor = mock_cursor
    return manager


def test_get_companies_and_vacancies_count(mock_db_manager):
    """Тест подсчета количества вакансий по компаниям."""
    mock_db_manager._test_cursor.fetchall.return_value = [("Яндекс", 15), ("Сбер", 8)]

    result = mock_db_manager.get_companies_and_vacancies_count()

    assert len(result) == 2
    assert result[0] == ("Яндекс", 15)
    mock_db_manager._test_cursor.execute.assert_called_once()


def test_get_avg_salary(mock_db_manager):
    """Тест корректного расчета средней зарплаты."""
    mock_db_manager._test_cursor.fetchone.return_value = (350000.0,)

    result = mock_db_manager.get_avg_salary()

    assert result == 350000.0
    mock_db_manager._test_cursor.execute.assert_called_once()


def test_get_vacancies_with_keyword(mock_db_manager):
    """Тест поиска вакансий по ключевому слову."""
    mock_db_manager._test_cursor.fetchall.return_value = [
        ("Тинькофф", "Python-разработчик", 200000, 300000, "RUB", "http://hh.ru")
    ]

    result = mock_db_manager.get_vacancies_with_keyword("python")

    assert len(result) == 1
    assert result[0][1] == "Python-разработчик"
    mock_db_manager._test_cursor.execute.assert_called_once()
