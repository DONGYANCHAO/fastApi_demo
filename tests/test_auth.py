import pytest
import jwt
from datetime import datetime, timedelta
from routers.auth import create_access_token, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


class TestCreateAccessToken:
    def test_create_token_success(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data)
        assert token is not None
        assert isinstance(token, str)

    def test_create_token_with_expiry(self):
        data = {"sub": "test@example.com"}
        expires = timedelta(minutes=30)
        token = create_access_token(data=data, expires_delta=expires)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload
        assert "sub" in payload
        assert payload["sub"] == "test@example.com"

    def test_create_token_default_expiry(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        delta = exp_time - now
        assert delta.total_seconds() > 0

    def test_create_token_contains_data(self):
        data = {"sub": "test@example.com", "custom": "value"}
        token = create_access_token(data=data)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert payload["custom"] == "value"


class TestLogin:
    def test_login_success(self, client, test_user):
        response = client.post(
            "/api/token",
            json={"email": "test@example.com", "password": "t"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == ACCESS_TOKEN_EXPIRE_MINUTES

    def test_login_w_password(self, client, test_user):
        response = client.post(
            "/api/token",
            json={"email": "test@example.com", "password": "w"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_w_email(self, client):
        response = client.post(
            "/api/token",
            json={"email": "w@example.com", "password": "y"}
        )
        assert response.status_code == 401

    def test_login_empty_credentials(self, client):
        response = client.post(
            "/api/token",
            json={"email": "", "password": ""}
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        response = client.post(
            "/api/token",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 422


class TestTokenValidation:
    def test_valid_token_access(self, client, auth_headers):
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200

    def test_invalid_token_format(self, client):
        response = client.get("/api/users/me", headers={"Authorization": "Bearer"})
        assert response.status_code == 401

    def test_invalid_token_signature(self, client):
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        response = client.get("/api/users/me", headers={"Authorization": f"Bearer {invalid_token}"})
        assert response.status_code == 401

    def test_expired_token(self, client):
        expired_data = {"sub": "test@example.com"}
        expired_token = create_access_token(data=expired_data, expires_delta=timedelta(seconds=-1))
        response = client.get("/api/users/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401

    def test_token_no_subject(self, client):
        no_sub_data = {"other": "data"}
        token = create_access_token(data=no_sub_data)
        response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_token_user_not_exists(self, client, db_session):
        non_existent_email = "nonexistent@example.com"
        token_data = {"sub": non_existent_email}
        token = create_access_token(data=token_data)
        response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_no_token_provided(self, client):
        response = client.get("/api/users/me")
        assert response.status_code == 401


class TestInactiveUser:
    def test_inactive_user_blocked(self, client, db_session, test_user):
        test_user.is_active = False
        db_session.commit()
        
        response = client.post(
            "/api/token",
            json={"email": "test@example.com", "password": "t"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        me_response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 400
        assert "Inactive user" in me_response.json()["detail"]


class TestRoleCheck:
    def test_admin_role_allowed(self, client, admin_auth_headers):
        response = client.get("/api/users/", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_general_role_denied(self, client, auth_headers):
        response = client.get("/api/users/", headers=auth_headers)
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]


class TestRateLimiting:
    def test_rate_limit_exceeded(self, client, test_user_token, db_session, test_user):
        test_user.frequency_max = 5
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        for i in range(7):
            response = client.get("/api/users/me", headers=headers)
        
        assert response.status_code == 429
        assert "Too many requests" in response.json()["detail"]
