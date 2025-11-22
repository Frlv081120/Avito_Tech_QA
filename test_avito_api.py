import pytest
import requests
import random
import time
from typing import Dict, Any

BASE_URL = "https://qa-internship.avito.com"


class TestAvitoAPI:
    """Тесты для API микросервиса объявлений"""

    @pytest.fixture
    def unique_seller_id(self) -> int:
        """Генерация уникального sellerId"""
        return random.randint(111111, 999999)

    @pytest.fixture
    def sample_item_data(self, unique_seller_id: int) -> Dict[str, Any]:
        """Фикстура с данными для создания объявления"""
        return {
            "sellerId": unique_seller_id,
            "title": f"Test Item {int(time.time())}",
            "description": "Test description for the item",
            "price": 1000,
            "picture": "https://example.com/image.jpg"
        }

    def test_create_item_positive(self, sample_item_data: Dict[str, Any]):
        """TC-001: Успешное создание объявления"""
        response = requests.post(f"{BASE_URL}/api/items", json=sample_item_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["sellerId"] == sample_item_data["sellerId"]
        assert data["title"] == sample_item_data["title"]
        assert data["description"] == sample_item_data["description"]
        assert data["price"] == sample_item_data["price"]
        assert data["picture"] == sample_item_data["picture"]
        assert "id" in data and data["id"]
        assert "createdAt" in data and data["createdAt"]

    def test_get_item_by_id_positive(self, sample_item_data: Dict[str, Any]):
        """TC-002: Получение объявления по существующему ID"""
        # Создаем объявление
        create_response = requests.post(f"{BASE_URL}/api/items", json=sample_item_data)
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]
        
        # Получаем объявление по ID
        get_response = requests.get(f"{BASE_URL}/api/items/{item_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == item_id
        assert data["sellerId"] == sample_item_data["sellerId"]
        assert data["title"] == sample_item_data["title"]

    def test_get_items_by_seller_id_positive(self, unique_seller_id: int):
        """TC-003: Получение всех объявлений по sellerId"""
        # Создаем два объявления с одинаковым sellerId
        item_data = {
            "sellerId": unique_seller_id,
            "title": f"First Item {int(time.time())}",
            "description": "First test item",
            "price": 1000,
            "picture": "https://example.com/image1.jpg"
        }
        
        response1 = requests.post(f"{BASE_URL}/api/items", json=item_data)
        assert response1.status_code == 200
        
        item_data["title"] = f"Second Item {int(time.time())}"
        item_data["description"] = "Second test item"
        response2 = requests.post(f"{BASE_URL}/api/items", json=item_data)
        assert response2.status_code == 200
        
        # Получаем все объявления продавца
        get_response = requests.get(f"{BASE_URL}/api/items?sellerId={unique_seller_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert "items" in data
        assert len(data["items"]) >= 2
        
        # Проверяем, что все объявления принадлежат указанному sellerId
        for item in data["items"]:
            assert item["sellerId"] == unique_seller_id

    def test_get_item_stats_positive(self, sample_item_data: Dict[str, Any]):
        """TC-004: Получение статистики по существующему itemId"""
        # Создаем объявление
        create_response = requests.post(f"{BASE_URL}/api/items", json=sample_item_data)
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]
        
        # Получаем статистику
        stats_response = requests.get(f"{BASE_URL}/api/items/{item_id}/stats")
        
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["itemId"] == item_id
        assert "views" in stats_data
        assert "clicks" in stats_data
        assert isinstance(stats_data["views"], int)
        assert isinstance(stats_data["clicks"], int)

    def test_create_item_negative_missing_fields(self):
        """TC-005: Создание объявления с невалидными данными (отсутствуют обязательные поля)"""
        invalid_data = {
            "title": "Test Item",
            # Отсутствует sellerId, price и другие обязательные поля
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=invalid_data)
        
        # Ожидаем ошибку клиента
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"

    def test_get_item_by_id_negative(self):
        """TC-006: Получение объявления по несуществующему ID"""
        non_existent_id = "non_existent_id_12345"
        
        response = requests.get(f"{BASE_URL}/api/items/{non_existent_id}")
        
        assert response.status_code == 404

    def test_get_items_by_seller_id_negative(self):
        """TC-007: Получение объявлений по несуществующему sellerId"""
        non_existent_seller_id = 123456  # Предполагаем, что такого нет
        
        response = requests.get(f"{BASE_URL}/api/items?sellerId={non_existent_seller_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0

    def test_get_item_stats_negative(self):
        """TC-008: Получение статистики по несуществующему itemId"""
        non_existent_id = "non_existent_id_12345"
        
        response = requests.get(f"{BASE_URL}/api/items/{non_existent_id}/stats")
        
        assert response.status_code == 404

    def test_create_item_negative_negative_price(self, unique_seller_id: int):
        """TC-009: Создание объявления с отрицательной ценой"""
        invalid_data = {
            "sellerId": unique_seller_id,
            "title": "Test Item with Negative Price",
            "description": "Test description",
            "price": -100,
            "picture": "https://example.com/image.jpg"
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=invalid_data)
        
        # Ожидаем ошибку валидации
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"

    def test_create_item_boundary_values(self, unique_seller_id: int):
        """TC-010: Создание объявления с boundary значениями"""
        # Тест с очень длинными значениями
        long_string = "A" * 1000
        
        boundary_data = {
            "sellerId": unique_seller_id,
            "title": long_string,
            "description": long_string,
            "price": 0,  # Минимальная цена
            "picture": "https://example.com/image.jpg"
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=boundary_data)
        
        # Проверяем, что сервер обрабатывает boundary значения
        # Может вернуть 200 или 400 в зависимости от валидации
        assert response.status_code in [200, 400], f"Unexpected status code: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])