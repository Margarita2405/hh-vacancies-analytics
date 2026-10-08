from unittest.mock import MagicMock, patch

from src.utils import create_database, create_tables


@patch("psycopg2.connect")
def test_create_database_not_exists(mock_connect):
    """Тест создания базы данных, если она изначально не существует."""
    # Настраиваем цепочку моков для соединений и курсоров
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_connect.return_value = mock_conn

    # Имитируем, что fetchone() вернул None (база данных не найдена)
    mock_cur.fetchone.return_value = None

    create_database()

    # Проверяем, что autocommit был принудительно включен в True
    assert mock_conn.autocommit is True

    # Проверяем, что SQL-запрос на создание базы данных был вызван
    # В вызовах должно быть как минимум 2 execute: проверка и создание
    assert mock_cur.execute.call_count == 2
    mock_cur.execute.assert_any_call("CREATE DATABASE hh_parser")

    # Проверяем, что ресурсы корректно закрылись
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("psycopg2.connect")
def test_create_database_already_exists(mock_connect):
    """Тест поведения функции, если база данных уже существует."""
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_connect.return_value = mock_conn

    # Имитируем, что fetchone() вернул (1,) (база данных уже есть)
    mock_cur.fetchone.return_value = (1,)

    create_database()

    # Проверяем, что был только 1 запрос (проверка) и CREATE DATABASE НЕ вызывался
    mock_cur.execute.assert_called_once()
    assert mock_cur.execute.call_count == 1

    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("psycopg2.connect")
def test_create_tables(mock_connect):
    """Тест успешного создания таблиц в целевой базе данных."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    # Настраиваем мок под контекстный менеджер: with psycopg2.connect() as conn:
    mock_connect.return_value.__enter__.return_value = mock_conn
    # Настраиваем мок под контекстный менеджер курсора: with conn.cursor() as cur:
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    create_tables()

    # Проверяем, что execute выполнил DDL-скрипт создания таблиц
    mock_cur.execute.assert_called_once()
    # Проверяем, что в SQL-запросе фигурируют имена наших целевых таблиц
    sql_arg = mock_cur.execute.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS employers" in sql_arg
    assert "CREATE TABLE IF NOT EXISTS vacancies" in sql_arg
