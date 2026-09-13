"""
Inventory API tests
"""
import pytest
import os

# BASE_URL: Use environment variable if available, otherwise fallback to production URL
# Import BASE_URL from conftest
from tests.conftest import BASE_URL
BASE_URL = BASE_URL.rstrip('/')


class TestInventory:
    """Inventory endpoint tests"""
    
    def test_get_product_inventory(self, api_client, sample_product_id):
        """Test getting inventory for a product"""
        if not sample_product_id:
            pytest.skip("No sample product available")
        
        response = api_client.get(f"{BASE_URL}/api/inventory/{sample_product_id}")
        
        # Status assertion
        assert response.status_code == 200, f"Get inventory failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "id" in data
        assert "product_id" in data
        assert "quantity" in data
        assert "reserved" in data
        assert "available" in data
        assert "is_low_stock" in data
        assert "is_out_of_stock" in data
        assert data["product_id"] == sample_product_id
    
    def test_get_inventory_not_found(self, api_client):
        """Test getting inventory for non-existent product returns 404"""
        fake_id = "non-existent-product-id-12345"
        response = api_client.get(f"{BASE_URL}/api/inventory/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_available_stock(self, api_client, sample_product_id):
        """Test getting available stock for a product"""
        if not sample_product_id:
            pytest.skip("No sample product available")
        
        response = api_client.get(f"{BASE_URL}/api/inventory/{sample_product_id}/available")
        
        # Status assertion
        assert response.status_code == 200, f"Get available stock failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "product_id" in data
        assert "available" in data
        assert data["product_id"] == sample_product_id
        assert isinstance(data["available"], int)
