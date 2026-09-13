"""
Authentication API tests - Register and Login endpoints
"""
import pytest
import uuid
import os

# Import BASE_URL from conftest
from tests.conftest import BASE_URL


class TestAuthRegister:
    """User registration tests"""
    
    def test_register_new_user_success(self, api_client):
        """Test successful user registration"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_user_{unique_id}@polluxkart.com",
            "phone": f"+91{unique_id}99999",
            "name": f"Test User {unique_id}",
            "password": "TestPass@123"
        }
        
        response = api_client.post(f"{BASE_URL}/api/auth/register", json=user_data)
        
        # Status assertion
        assert response.status_code == 201, f"Registration failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["name"] == user_data["name"]
        assert data["user"]["phone"] == user_data["phone"]
        assert "id" in data["user"]
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
    
    def test_register_duplicate_phone_fails(self, api_client, test_user_phone, ensure_test_user):
        """Test registration with duplicate phone fails"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_dup_{unique_id}@polluxkart.com",
            "phone": test_user_phone,  # Same as test user
            "name": "Duplicate User",
            "password": "TestPass@123"
        }
        
        response = api_client.post(f"{BASE_URL}/api/auth/register", json=user_data)
        
        # Should fail with 400
        assert response.status_code == 400
    
    def test_register_missing_required_fields(self, api_client):
        """Test registration with missing fields fails"""
        user_data = {
            "email": "incomplete@test.com"
            # Missing phone, name, password
        }
        
        response = api_client.post(f"{BASE_URL}/api/auth/register", json=user_data)
        
        # Should fail with 422 (validation error)
        assert response.status_code == 422


class TestAuthLogin:
    """User login tests"""
    
    def test_login_with_email_success(self, api_client, test_user_credentials, ensure_test_user):
        """Test successful login with email"""
        # Skip if test user couldn't be created
        if not ensure_test_user:
            pytest.skip("Test user could not be created")
        
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json=test_user_credentials
        )
        
        # Status assertion
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert "id" in data["user"]
        assert "name" in data["user"]
    
    def test_login_with_phone_success(self, api_client, ensure_test_user):
        """Test successful login with phone number"""
        # Skip if test user couldn't be created
        if not ensure_test_user:
            pytest.skip("Test user could not be created")
        
        # Get the actual phone from ensure_test_user
        user_phone = ensure_test_user.get("user", {}).get("phone")
        if not user_phone:
            pytest.skip("Test user has no phone number")
        
        login_data = {
            "identifier": user_phone,
            "password": "Test@123"
        }
        
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        # Status assertion
        assert response.status_code == 200, f"Login with phone failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "access_token" in data
        assert "user" in data
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials fails"""
        login_data = {
            "identifier": "wrong@example.com",
            "password": "wrongpassword"
        }
        
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        # Should fail with 401
        assert response.status_code == 401
        
        # Data assertion - validate error response
        data = response.json()
        assert "detail" in data
    
    def test_login_wrong_password(self, api_client, test_user_credentials):
        """Test login with wrong password fails"""
        login_data = {
            "identifier": test_user_credentials["identifier"],
            "password": "WrongPassword123"
        }
        
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        # Should fail with 401
        assert response.status_code == 401
