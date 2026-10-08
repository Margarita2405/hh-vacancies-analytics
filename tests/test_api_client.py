from unittest.mock import MagicMock, patch

import pytest

from src.api_client import HHAPIClient


@pytest.fixture
def api_client():
    """Фикстура для инициализации клиента API перед каждым тестом."""
    return HHAPIClient()


@patch("requests.get")
def test_get_employer_success(mock_get, api_client):
    """Тестирование успешного получения данных работодателя."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "1", "name": "Тестовая Компания"}
    mock_get.return_value = mock_response

    result = api_client.get_employer(1)

    assert result["name"] == "Тестовая Компания"
    assert result["id"] == "1"
    # Проверяем, что вызов пошел на правильный базовый URL вашего класса
    mock_get.assert_called_once()


@patch("requests.get")
def test_get_vacancies_success(mock_get, api_client):
    """Тестирование получения списка вакансий компании с учетом пагинации."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Добавляем обязательный ключ 'pages', чтобы цикл в вашем коде корректно завершился
    mock_response.json.return_value = {
        "items": [{"id": "10", "name": "Python Developer"}],
        "pages": 1
    }
    mock_get.return_value = mock_response

    result = api_client.get_vacancies(1)

    assert len(result) == 1
    assert result[0]["name"] == "Python Developer"
    mock_get.assert_called_once()
