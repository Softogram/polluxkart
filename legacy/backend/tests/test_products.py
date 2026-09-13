"""
Products API tests - List, filter, sort, get single product, reviews
"""
import pytest
import os

# Import BASE_URL from conftest
from tests.conftest import BASE_URL


class TestProductsList:
    """Product listing and filtering tests"""
    
    def test_get_products_default(self, api_client):
        """Test getting products with default pagination"""
        response = api_client.get(f"{BASE_URL}/api/products")
        
        # Status assertion
        assert response.status_code == 200, f"Get products failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert isinstance(data["products"], list)
        assert data["page"] == 1
        assert data["page_size"] == 12  # Default page size
    
    def test_get_products_with_pagination(self, api_client):
        """Test products pagination"""
        response = api_client.get(f"{BASE_URL}/api/products?page=1&page_size=5")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["products"]) <= 5
    
    def test_get_products_sort_by_price_asc(self, api_client):
        """Test sorting products by price ascending"""
        response = api_client.get(f"{BASE_URL}/api/products?sort_by=price_asc&page_size=10")
        
        assert response.status_code == 200
        
        data = response.json()
        products = data["products"]
        if len(products) > 1:
            prices = [p["price"] for p in products]
            assert prices == sorted(prices), "Products not sorted by price ascending"
    
    def test_get_products_sort_by_price_desc(self, api_client):
        """Test sorting products by price descending"""
        response = api_client.get(f"{BASE_URL}/api/products?sort_by=price_desc&page_size=10")
        
        assert response.status_code == 200
        
        data = response.json()
        products = data["products"]
        if len(products) > 1:
            prices = [p["price"] for p in products]
            assert prices == sorted(prices, reverse=True), "Products not sorted by price descending"
    
    def test_get_products_filter_by_search(self, api_client):
        """Test searching products"""
        response = api_client.get(f"{BASE_URL}/api/products?search=phone")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        # Search results should contain matching products
    
    def test_get_products_filter_in_stock_only(self, api_client):
        """Test filtering in-stock products only"""
        response = api_client.get(f"{BASE_URL}/api/products?in_stock_only=true")
        
        assert response.status_code == 200
        
        data = response.json()
        products = data["products"]
        for product in products:
            assert product["in_stock"] == True, f"Product {product['id']} should be in stock"
    
    def test_get_products_filter_by_price_range(self, api_client):
        """Test filtering products by price range"""
        min_price = 100
        max_price = 1000
        response = api_client.get(f"{BASE_URL}/api/products?min_price={min_price}&max_price={max_price}")
        
        assert response.status_code == 200
        
        data = response.json()
        products = data["products"]
        for product in products:
            assert product["price"] >= min_price, f"Product price {product['price']} below min"
            assert product["price"] <= max_price, f"Product price {product['price']} above max"


class TestProductsCategories:
    """Category endpoint tests"""
    
    def test_get_categories(self, api_client, ensure_test_category):
        """Test getting all categories"""
        response = api_client.get(f"{BASE_URL}/api/products/categories")
        
        # Status assertion
        assert response.status_code == 200, f"Get categories failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert isinstance(data, list)
        # In CI with empty database, we may have 0 or 1 category (from ensure_test_category)
        # Only assert structure if categories exist
        if len(data) > 0:
            # Verify category structure
            for category in data:
                assert "id" in category
                assert "name" in category
    
    def test_get_categories_with_subcategories(self, api_client, ensure_test_category):
        """Test categories include subcategories"""
        response = api_client.get(f"{BASE_URL}/api/products/categories?include_subcategories=true")
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Check if subcategories field exists (only if we have categories)
        for category in data:
            assert "subcategories" in category


class TestProductsBrands:
    """Brand endpoint tests"""
    
    def test_get_brands(self, api_client):
        """Test getting all brands"""
        response = api_client.get(f"{BASE_URL}/api/products/brands")
        
        # Status assertion
        assert response.status_code == 200, f"Get brands failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert isinstance(data, list)


class TestSingleProduct:
    """Single product endpoint tests"""
    
    def test_get_product_by_id(self, api_client, sample_product_id):
        """Test getting a single product by ID"""
        if not sample_product_id:
            pytest.skip("No sample product available")
        
        response = api_client.get(f"{BASE_URL}/api/products/{sample_product_id}")
        
        # Status assertion
        assert response.status_code == 200, f"Get product failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data["id"] == sample_product_id
        assert "name" in data
        assert "price" in data
        assert "description" in data
        assert "category_id" in data
        assert "in_stock" in data
    
    def test_get_product_not_found(self, api_client):
        """Test getting non-existent product returns 404"""
        fake_id = "non-existent-product-id-12345"
        response = api_client.get(f"{BASE_URL}/api/products/{fake_id}")
        
        assert response.status_code == 404


class TestProductReviews:
    """Product reviews endpoint tests"""
    
    def test_get_product_reviews(self, api_client, sample_product_id):
        """Test getting reviews for a product"""
        if not sample_product_id:
            pytest.skip("No sample product available")
        
        response = api_client.get(f"{BASE_URL}/api/products/{sample_product_id}/reviews")
        
        # Status assertion
        assert response.status_code == 200, f"Get reviews failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert isinstance(data, list)
        
        # If reviews exist, verify structure
        for review in data:
            assert "id" in review
            assert "rating" in review
            assert "user_name" in review
