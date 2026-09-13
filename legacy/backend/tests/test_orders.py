"""
Orders API tests - Requires authentication
"""
import pytest
import os

# BASE_URL: Use environment variable if available, otherwise fallback to production URL
# Import BASE_URL from conftest
from tests.conftest import BASE_URL
BASE_URL = BASE_URL.rstrip('/')


class TestOrders:
    """Order endpoint tests - requires authentication"""
    
    def test_get_orders_requires_auth(self, api_client):
        """Test that orders endpoint requires authentication"""
        # Remove auth header if present
        api_client.headers.pop("Authorization", None)
        
        response = api_client.get(f"{BASE_URL}/api/orders")
        
        # Should fail with 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
    
    def test_get_orders_authenticated(self, authenticated_client):
        """Test getting orders with authentication"""
        response = authenticated_client.get(f"{BASE_URL}/api/orders")
        
        # Status assertion
        assert response.status_code == 200, f"Get orders failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "orders" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["orders"], list)
    
    def test_get_orders_with_pagination(self, authenticated_client):
        """Test orders pagination"""
        response = authenticated_client.get(f"{BASE_URL}/api/orders?page=1&page_size=5")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    def test_create_order_empty_cart_fails(self, authenticated_client):
        """Test creating order with empty cart fails"""
        # First clear the cart
        authenticated_client.delete(f"{BASE_URL}/api/cart")
        
        order_data = {
            "shipping_address": {
                "full_name": "Test User",
                "phone": "+919999999999",
                "address_line1": "123 Test Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "country": "India"
            },
            "payment_method": "cod"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/orders", json=order_data)
        
        # Should fail with 400 (cart is empty)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
    
    def test_create_order_with_items(self, authenticated_client, sample_product_id):
        """Test creating order with items in cart"""
        if not sample_product_id:
            pytest.skip("No sample product available")
        
        # First add item to cart
        item_data = {
            "product_id": sample_product_id,
            "quantity": 1
        }
        cart_response = authenticated_client.post(f"{BASE_URL}/api/cart/items", json=item_data)
        
        if cart_response.status_code != 200:
            pytest.skip("Could not add item to cart")
        
        # Create order
        order_data = {
            "shipping_address": {
                "full_name": "Test User",
                "phone": "+919999999999",
                "address_line1": "123 Test Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "country": "India"
            },
            "payment_method": "cod"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/orders", json=order_data)
        
        # Status assertion
        assert response.status_code == 201, f"Create order failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "id" in data
        assert "order_number" in data
        assert "items" in data
        assert "total" in data
        assert "status" in data
        assert data["status"] == "pending"
        assert len(data["items"]) > 0
