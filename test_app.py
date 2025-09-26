
import pytest
from main import app as flask_app

@pytest.fixture
def app(mocker):
    mocker.patch("firebase_admin.credentials.Certificate")
    mocker.patch("firebase_admin.initialize_app")
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_admin_login_page(client):
    """Tests if the admin login page loads correctly."""
    response = client.get("/admin_login")
    assert response.status_code == 200
    assert b"Admin Login" in response.data
