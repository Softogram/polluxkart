"""
Pytest configuration and shared fixtures for PolluxKart API tests
"""
import pytest
import requests
import os
import time

# Get BASE_URL from environment - check frontend env first, then fallback to backend URL
# In CI, use localhost:8001
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL') or os.environ.get('API_BASE_URL')
if not BASE_URL:
    # Default to localhost for CI environment
    BASE_URL = 'http://localhost:8001'
BASE_URL = BASE_URL.rstrip('/')
print(f"Test BASE_URL: {BASE_URL}")

# Admin setup key for creating initial admin
ADMIN_SETUP_KEY = os.environ.get('ADMIN_SETUP_KEY', 'POLLUXKART_INITIAL_ADMIN_2025')

@pytest.fixture(scope="session")
def base_url():
    """Return the base URL for API calls"""
    return BASE_URL

@pytest.fixture(scope="function")
def api_client():
    """Shared requests session - function scope to avoid header pollution"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="session")
def test_user_credentials():
    """Test user credentials"""
    return {
        "identifier": "test@polluxkart.com",
        "password": "Test@123"
    }

@pytest.fixture(scope="session")
def test_user_phone():
    """Test user phone number"""
    return "+919876543210"

@pytest.fixture(scope="session")
def admin_credentials():
    """Admin user credentials"""
    return {
        "identifier": "admin@polluxkart.com",
        "password": "Admin@123"
    }

@pytest.fixture(scope="session")
def ensure_test_user(base_url):
    """Ensure test user exists in the database"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Try to login first
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"identifier": "test@polluxkart.com", "password": "Test@123"}
    )
    
    if login_response.status_code == 200:
        return login_response.json()
    
    # If login fails, register the user
    register_data = {
        "email": "test@polluxkart.com",
        "phone": "+919876543210",
        "name": "Test User",
        "password": "Test@123"
    }
    reg_response = session.post(f"{base_url}/api/auth/register", json=register_data)
    if reg_response.status_code in [200, 201]:
        return reg_response.json()
    
    return None

@pytest.fixture(scope="session")
def ensure_admin_user(base_url):
    """Ensure admin user exists in the database for testing"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Try to login as admin first
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"identifier": "admin@polluxkart.com", "password": "Admin@123"}
    )
    
    if login_response.status_code == 200:
        data = login_response.json()
        # Check if user has admin role
        if data.get("user", {}).get("role") in ["admin", "super_admin"]:
            return data
    
    # Check if admin setup is available
    setup_response = session.get(f"{base_url}/api/admin/setup/status")
    if setup_response.status_code == 200:
        setup_data = setup_response.json()
        
        if setup_data.get("setup_available"):
            # Create initial admin using the setup endpoint
            admin_data = {
                "email": "admin@polluxkart.com",
                "phone": "+919999999999",
                "name": "Test Admin",
                "password": "Admin@123",
                "setup_key": ADMIN_SETUP_KEY
            }
            create_response = session.post(
                f"{base_url}/api/admin/setup/initial-admin",
                json=admin_data
            )
            
            if create_response.status_code in [200, 201]:
                # Now login to get the token
                login_response = session.post(
                    f"{base_url}/api/auth/login",
                    json={"identifier": "admin@polluxkart.com", "password": "Admin@123"}
                )
                if login_response.status_code == 200:
                    return login_response.json()
    
    return None

@pytest.fixture(scope="session")
def auth_token(base_url, ensure_test_user):
    """Get authentication token for test user"""
    if ensure_test_user and "access_token" in ensure_test_user:
        return ensure_test_user["access_token"]
    
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    response = session.post(
        f"{base_url}/api/auth/login",
        json={"identifier": "test@polluxkart.com", "password": "Test@123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="session")
def admin_token(base_url, ensure_admin_user):
    """Get authentication token for admin user"""
    if ensure_admin_user and "access_token" in ensure_admin_user:
        return ensure_admin_user["access_token"]
    
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    response = session.post(
        f"{base_url}/api/auth/login",
        json={"identifier": "admin@polluxkart.com", "password": "Admin@123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    
    pytest.skip("Admin authentication failed - skipping admin tests")

@pytest.fixture(scope="function")
def authenticated_client(admin_token):
    """Session with admin auth header - function scope for clean state"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    })
    return session

@pytest.fixture(scope="function")
def user_client(auth_token):
    """Session with regular user auth header - function scope for clean state"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session

@pytest.fixture(scope="session")
def ensure_test_category(base_url, admin_token):
    """Ensure at least one category exists for testing"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    })
    
    # Check if categories exist
    response = session.get(f"{base_url}/api/products/categories")
    if response.status_code == 200:
        categories = response.json()
        if categories and len(categories) > 0:
            return categories[0]
    
    # Create a test category if none exist
    category_data = {
        "name": "Test Category",
        "description": "Category created for testing",
        "is_active": True
    }
    create_response = session.post(f"{base_url}/api/admin/categories", json=category_data)
    if create_response.status_code in [200, 201]:
        return create_response.json()
    
    return None

@pytest.fixture(scope="session")
def sample_product_id(base_url):
    """Get a sample product ID from the database"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.get(f"{base_url}/api/products?page_size=1")
    if response.status_code == 200:
        products = response.json().get("products", [])
        if products:
            return products[0]["id"]
    return None

@pytest.fixture(scope="function")
def unique_promo_code():
    """Generate a unique promotion code for each test"""
    return f"TEST{int(time.time() * 1000)}"
