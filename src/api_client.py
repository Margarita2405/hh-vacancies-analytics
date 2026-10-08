from typing import Any, Dict, List, cast

import requests


class HHAPIClient:
    """Класс для работы с публичным API hh.ru."""

    def __init__(
        self, base_url: str = "https://api.hh.ru", user_agent: str = "Course_work3/1.0 (mbursheva@mail.ru)"
    ) -> None:
        self.base_url = base_url
        self.headers = {"User-Agent": user_agent}

    def get_employer(self, employer_id: int) -> Dict[str, Any]:
        """Получить информацию о работодателе по ID."""
        url = f"{self.base_url}/employers/{employer_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return cast(Dict[str, Any], response.json())

    def get_vacancies(self, employer_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """Получить список вакансий для указанного работодателя."""
        vacancies = []
        page = 0
        while True:
            params = {"employer_id": employer_id, "per_page": per_page, "page": page}
            response = requests.get(f"{self.base_url}/vacancies", headers=self.headers, params=params)
            response.raise_for_status()
            data = cast(Dict[str, Any], response.json())
            vacancies.extend(data["items"])
            if page >= data["pages"] - 1:
                break
            page += 1
        return vacancies
