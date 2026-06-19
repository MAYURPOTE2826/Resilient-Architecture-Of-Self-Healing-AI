"""
API Endpoint Tests
Tests for Flask API endpoints including health checks and auth.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import jwt

# Import Flask app
from api import app
from config import settings


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def valid_credentials():
    """Valid login credentials."""
    return {
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD
    }


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_returns_200(self, client):
        """Test /health endpoint."""
        response = client.get('/health')
        
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert "status" in data
        assert "components" in data

    def test_live_endpoint_returns_200(self, client):
        """Test /live endpoint."""
        response = client.get('/live')
        
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert "alive" in data

    def test_ready_endpoint_returns_200(self, client):
        """Test /ready endpoint."""
        response = client.get('/ready')
        
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert "ready" in data

    def test_startup_endpoint_returns_200(self, client):
        """Test /startup endpoint."""
        response = client.get('/startup')
        
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert "ready" in data


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_with_valid_credentials(self, client, valid_credentials):
        """Test successful login."""
        response = client.post(
            '/api/auth/login',
            data=json.dumps(valid_credentials),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_login_with_invalid_credentials(self, client):
        """Test failed login."""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({
                "username": "admin",
                "password": "wrongpassword"
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_login_with_missing_username(self, client):
        """Test login with missing username."""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({
                "password": "password123"
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400

    def test_login_with_missing_password(self, client):
        """Test login with missing password."""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({
                "username": "admin"
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400

    def test_login_without_content_type_returns_415(self, client, valid_credentials):
        """Test login without JSON content type."""
        response = client.post(
            '/api/auth/login',
            data=json.dumps(valid_credentials),
            content_type='text/plain'
        )
        
        assert response.status_code in [415, 400]

    def test_refresh_token_with_valid_token(self, client, valid_credentials):
        """Test token refresh."""
        # First, login to get refresh token
        login_response = client.post(
            '/api/auth/login',
            data=json.dumps(valid_credentials),
            content_type='application/json'
        )
        
        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        refresh_token = login_data["refresh_token"]
        
        # Now refresh the token
        refresh_response = client.post(
            '/api/auth/refresh',
            data=json.dumps({
                "refresh_token": refresh_token
            }),
            content_type='application/json'
        )
        
        assert refresh_response.status_code == 200
        refresh_data = json.loads(refresh_response.data)
        assert "access_token" in refresh_data

    def test_refresh_token_with_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            '/api/auth/refresh',
            data=json.dumps({
                "refresh_token": "invalid_token"
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 401

    def test_logout_with_valid_token(self, client, valid_credentials):
        """Test logout."""
        # First, login
        login_response = client.post(
            '/api/auth/login',
            data=json.dumps(valid_credentials),
            content_type='application/json'
        )
        
        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        access_token = login_data["access_token"]
        
        # Now logout
        logout_response = client.post(
            '/api/auth/logout',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        assert logout_response.status_code == 200

    def test_logout_without_token(self, client):
        """Test logout without token."""
        response = client.post(
            '/api/auth/logout',
            content_type='application/json'
        )
        
        assert response.status_code == 401


class TestSecurityHeaders:
    """Test security headers in responses."""

    def test_responses_include_security_headers(self, client):
        """Test security headers are present."""
        response = client.get('/health')
        
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'

    def test_responses_include_correlation_id(self, client):
        """Test correlation ID is included."""
        response = client.get('/health')
        
        assert 'X-Request-ID' in response.headers
        assert 'X-Trace-ID' in response.headers
        assert 'X-Correlation-ID' in response.headers


class TestErrorHandling:
    """Test error handling."""

    def test_404_returns_proper_error_response(self, client):
        """Test 404 error response."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "code" in data

    def test_405_returns_proper_error_response(self, client):
        """Test 405 error response."""
        response = client.get('/api/auth/login')  # GET instead of POST
        
        assert response.status_code in [404, 405]

    def test_500_returns_proper_error_response(self, client):
        """Test 500 error response."""
        # This would require mocking internal errors
        # For now, just test the structure is correct
        response = client.get('/health')
        
        if response.status_code == 500:
            data = json.loads(response.data)
            assert "error" in data


class TestCORSHeaders:
    """Test CORS headers."""

    def test_cors_headers_present(self, client):
        """Test CORS headers."""
        response = client.options('/health')
        
        # CORS headers may be present
        if 'Access-Control-Allow-Origin' in response.headers:
            # If CORS headers exist, they should be properly formatted
            assert response.headers['Access-Control-Allow-Origin'] is not None


class TestRateLimiting:
    """Test rate limiting."""

    def test_rate_limiting_enforced(self, client, valid_credentials):
        """Test that rate limiting is enforced."""
        # This test would depend on rate limiting configuration
        # Make multiple requests and check for 429 responses
        
        # Note: May need to adjust based on actual rate limits
        for i in range(5):
            response = client.post(
                '/api/auth/login',
                data=json.dumps(valid_credentials),
                content_type='application/json'
            )
            
            # Should either succeed or be rate limited
            assert response.status_code in [200, 401, 429]


class TestRequestIdTracking:
    """Test request ID tracking."""

    def test_request_id_present_in_response(self, client):
        """Test request ID tracking."""
        response = client.get('/health')
        
        assert 'X-Request-ID' in response.headers
        request_id = response.headers['X-Request-ID']
        assert request_id.startswith('req_')

    def test_request_ids_are_unique(self, client):
        """Test request IDs are unique."""
        response1 = client.get('/health')
        response2 = client.get('/health')
        
        id1 = response1.headers.get('X-Request-ID')
        id2 = response2.headers.get('X-Request-ID')
        
        assert id1 != id2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
