"""
Cart and Wishlist API tests - Requires authentication
"""
import pytest
import os

# BASE_URL: Use environment variable if available, otherwise fallback to production URL
# Import BASE_URL from conftest
from tests.conftest import BASE_URL
BASE_URL = BASE_URL.rstrip('/')


class TestCart:
    """Cart endpoint tests - requires authentication"""
    
    def test_get_cart_requires_auth(self, api_client):
        """Test that cart endpoint requires authentication"""
        # Remove auth header if present
        api_client.headers.pop("Authorization", None)
        
        response = api_client.get(f"{BASE_URL}/api/cart")
        
        # Should fail with 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
    
    def test_get_cart_authenticated(self, authenticated_client):
        """Test getting cart with authentication"""
        response = authenticated_client.get(f"{BASE_URL}/api/cart")
        
        # Status assertion
        assert response.status_code == 200, f"Get cart failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "items" in data
        assert "subtotal" in data
        assert "total" in data
        assert "item_count" in data
        assert isinstance(data["items"], list)
    
    def test_add_to_cart(self, authenticated_client, sample_product_id):
        """Test adding item to cart"""
        if not sample_product_id:
            pytest.skip("No sample product available")
        
        item_data = {
            "product_id": sample_product_id,
            "quantity": 1
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/cart/items", json=item_data)
        
        # Status assertion
        assert response.status_code == 200, f"Add to cart failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "items" in data
        assert data["item_count"] >= 1
        
        # Verify item was added
        product_ids = [item["product_id"] for item in data["items"]]
        assert sample_product_id in product_ids, "Product not found in cart"
    
    def test_add_to_cart_invalid_product(self, authenticated_client):
        """Test adding non-existent product to cart fails"""
        item_data = {
            "product_id": "non-existent-product-id",
            "quantity": 1
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/cart/items", json=item_data)
        
        # Should fail with 400
        assert response.status_code == 400


class TestWishlist:
    """Wishlist endpoint tests - requires authentication"""
    
    def test_get_wishlist_requires_auth(self, api_client):
        """Test that wishlist endpoint requires authentication"""
        # Remove auth header if present
        api_client.headers.pop("Authorization", None)
        
        response = api_client.get(f"{BASE_URL}/api/wishlist")
        
        # Should fail with 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
    
    def test_get_wishlist_authenticated(self, authenticated_client):
        """Test getting wishlist with authentication"""
        response = authenticated_client.get(f"{BASE_URL}/api/wishlist")
        
        # Status assertion
        assert response.status_code == 200, f"Get wishlist failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_add_to_wishlist(self, authenticated_client, sample_product_id):
        """Test adding item to wishlist"""
        if not sample_product_id:
            pytest.skip("No sample product available")
        
        item_data = {
            "product_id": sample_product_id
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/wishlist/items", json=item_data)
        
        # Status assertion
        assert response.status_code == 200, f"Add to wishlist failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "items" in data
        
        # Verify item was added
        product_ids = [item["product_id"] for item in data["items"]]
        assert sample_product_id in product_ids, "Product not found in wishlist"
    
    def test_add_to_wishlist_invalid_product(self, authenticated_client):
        """Test adding non-existent product to wishlist fails"""
        item_data = {
            "product_id": "non-existent-product-id"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/wishlist/items", json=item_data)
        
        # Should fail with 400
        assert response.status_code == 400
    
    def test_check_product_in_wishlist(self, authenticated_client, sample_product_id):
        """Test checking if product is in wishlist"""
        if not sample_product_id:
            pytest.skip("No sample product available")
        
        response = authenticated_client.get(f"{BASE_URL}/api/wishlist/check/{sample_product_id}")
        
        # Status assertion
        assert response.status_code == 200, f"Check wishlist failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "in_wishlist" in data
        assert isinstance(data["in_wishlist"], bool)
