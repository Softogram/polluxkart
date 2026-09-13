"""
Admin Authentication tests - Tests for admin role verification and protected routes
"""
import pytest
import os

# Import BASE_URL from conftest
from tests.conftest import BASE_URL


class TestAdminAuth:
    """Admin authentication and role verification tests"""
    
    def test_admin_login_returns_role(self, api_client, ensure_admin_user, admin_credentials):
        """Test that admin login returns user with admin role in response"""
        if not ensure_admin_user:
            pytest.skip("Admin user could not be created")
        
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
        
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert "role" in data["user"], "User response must include role field"
        assert data["user"]["role"] in ["admin", "super_admin"], f"Expected admin role, got {data['user'].get('role')}"
    
    def test_admin_dashboard_with_token(self, api_client, ensure_admin_user, admin_credentials):
        """Test admin dashboard API with valid admin token"""
        if not ensure_admin_user:
            pytest.skip("Admin user could not be created")
        
        # First login as admin
        login_response = api_client.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Request admin dashboard
        headers = {"Authorization": f"Bearer {token}"}
        dashboard_response = api_client.get(f"{BASE_URL}/api/admin/dashboard", headers=headers)
        
        assert dashboard_response.status_code == 200, f"Admin dashboard failed: {dashboard_response.text}"
        
        dashboard_data = dashboard_response.json()
        # Verify dashboard structure
        assert isinstance(dashboard_data, dict)
    
    def test_admin_products_endpoint_with_token(self, api_client, ensure_admin_user, admin_credentials):
        """Test that admin can access products list with token"""
        if not ensure_admin_user:
            pytest.skip("Admin user could not be created")
        
        # Login as admin
        login_response = api_client.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Access products (should work with pageSize=50 fix)
        headers = {"Authorization": f"Bearer {token}"}
        products_response = api_client.get(
            f"{BASE_URL}/api/products?page=1&page_size=50",
            headers=headers
        )
        
        assert products_response.status_code == 200, f"Products fetch failed: {products_response.text}"
        
        data = products_response.json()
        assert "products" in data
    
    def test_admin_products_large_pagesize_fails(self, api_client, ensure_admin_user, admin_credentials):
        """Test that very large pageSize returns 422 validation error"""
        if not ensure_admin_user:
            pytest.skip("Admin user could not be created")
        
        login_response = api_client.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try with page_size > 50 (the limit is 50)
        products_response = api_client.get(
            f"{BASE_URL}/api/products?page=1&page_size=100",
            headers=headers
        )
        
        # page_size > 50 should fail with 422
        assert products_response.status_code == 422, f"Expected 422 for page_size>50, got {products_response.status_code}"
    
    def test_protected_endpoint_without_token_fails(self, api_client):
        """Test that protected admin endpoints fail without token"""
        # Try to access admin dashboard without token
        response = api_client.get(f"{BASE_URL}/api/admin/dashboard")
        
        # Should fail with 401 or 403
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
    
    def test_regular_user_role_on_login(self, api_client, ensure_test_user):
        """Test that regular users get 'user' role on login"""
        if not ensure_test_user:
            pytest.skip("Test user could not be created")
        
        # Use test fixtures for regular user
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # Register new user
        register_data = {
            "email": f"TEST_regular_{unique_id}@polluxkart.com",
            "phone": f"+91{unique_id}12345",
            "name": f"Regular User {unique_id}",
            "password": "TestPass@123"
        }
        
        register_response = api_client.post(f"{BASE_URL}/api/auth/register", json=register_data)
        
        if register_response.status_code == 201:
            data = register_response.json()
            # New users should have 'user' role by default
            if "user" in data and "role" in data["user"]:
                assert data["user"]["role"] == "user", f"New user should have 'user' role, got {data['user']['role']}"
            else:
                # Role might not be returned on registration
                # Login to check
                login_data = {
                    "identifier": register_data["email"],
                    "password": register_data["password"]
                }
                login_response = api_client.post(f"{BASE_URL}/api/auth/login", json=login_data)
                if login_response.status_code == 200:
                    login_data_resp = login_response.json()
                    if "user" in login_data_resp and "role" in login_data_resp["user"]:
                        assert login_data_resp["user"]["role"] == "user"
    
    def test_regular_user_cannot_access_admin(self, api_client, ensure_test_user):
        """Test that regular users cannot access admin endpoints"""
        if not ensure_test_user:
            pytest.skip("Test user could not be created")
        
        # Create a new regular user to ensure they don't have admin role
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        register_data = {
            "email": f"TEST_noadmin_{unique_id}@polluxkart.com",
            "phone": f"+91{unique_id}54321",
            "name": f"Non-Admin User {unique_id}",
            "password": "TestPass@123"
        }
        
        register_response = api_client.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if register_response.status_code != 201:
            pytest.skip("Could not create test user")
        
        # Login as the new regular user
        login_data = {
            "identifier": register_data["email"],
            "password": register_data["password"]
        }
        login_response = api_client.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            pytest.skip("Could not login as test user")
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin dashboard
        dashboard_response = api_client.get(f"{BASE_URL}/api/admin/dashboard", headers=headers)
        
        # Regular user should be forbidden
        assert dashboard_response.status_code == 403, f"Expected 403 for regular user, got {dashboard_response.status_code}"


class TestJWTTokenRole:
    """Tests for JWT token containing role information"""
    
    def test_jwt_token_contains_role_claim(self, api_client, ensure_admin_user, admin_credentials):
        """Verify that the JWT token payload includes the role claim"""
        if not ensure_admin_user:
            pytest.skip("Admin user could not be created")
        
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
        assert response.status_code == 200
        
        data = response.json()
        token = data["access_token"]
        
        # Decode JWT (without verification) to check claims
        import base64
        import json
        
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) == 3:
            # Decode payload (add padding if needed)
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            
            payload_json = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_json)
            
            assert "role" in payload, "JWT token should contain 'role' claim"
            assert payload["role"] in ["admin", "super_admin"], f"Admin user JWT should have admin role, got {payload.get('role')}"
