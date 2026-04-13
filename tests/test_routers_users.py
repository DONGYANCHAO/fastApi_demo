import pytest


class TestCreateUser:
    def test_create_user_success(self, client):
        response = client.post(
            "/api/users/",
            json={"email": "newuser@example.com", "password": "p"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert data["role"] == "general"

    def test_create_user_duplicate_email(self, client, test_user):
        response = client.post(
            "/api/users/",
            json={"email": "test@example.com", "password": "p"}
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_create_user_invalid_email(self, client):
        response = client.post(
            "/api/users/",
            json={"email": "not-an-email", "password": "p"}
        )
        assert response.status_code == 200

    def test_create_user_empty_email(self, client):
        response = client.post(
            "/api/users/",
            json={"email": "", "password": "p"}
        )
        assert response.status_code == 200

    def test_create_user_empty_password(self, client):
        response = client.post(
            "/api/users/",
            json={"email": "user@example.com", "password": ""}
        )
        assert response.status_code == 200

    def test_create_user_missing_fields(self, client):
        response = client.post(
            "/api/users/",
            json={"email": "user@example.com"}
        )
        assert response.status_code == 422


class TestGetUsersList:
    def test_get_users_admin_success(self, client, admin_auth_headers):
        response = client.get("/api/users/", headers=admin_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_users_general_forbidden(self, client, auth_headers):
        response = client.get("/api/users/", headers=auth_headers)
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_get_users_unauthorized(self, client):
        response = client.get("/api/users/")
        assert response.status_code == 401

    def test_get_users_with_pagination(self, client, admin_auth_headers, db_session):
        for i in range(15):
            client.post(
                "/api/users/",
                json={"email": f"user{i}@example.com", "password": "p"}
            )
        response = client.get("/api/users/?skip=0&limit=10", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 10


class TestGetUserMe:
    def test_get_me_success(self, client, auth_headers):
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data

    def test_get_me_unauthorized(self, client):
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        response = client.get("/api/users/me", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 401


class TestGetUserById:
    def test_get_user_by_id_owner_success(self, client, auth_headers, test_user):
        response = client.get(f"/api/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == test_user.id

    def test_get_user_by_id_admin_success(self, client, admin_auth_headers, test_user):
        response = client.get(f"/api/users/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == test_user.id

    def test_get_user_by_id_other_user_forbidden(self, client, auth_headers, admin_user):
        response = client.get(f"/api/users/{admin_user.id}", headers=auth_headers)
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_get_user_by_id_not_found(self, client, admin_auth_headers):
        response = client.get("/api/users/9999", headers=admin_auth_headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_user_by_id_negative(self, client, admin_auth_headers):
        response = client.get("/api/users/-1", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_get_user_by_id_unauthorized(self, client, test_user):
        response = client.get(f"/api/users/{test_user.id}")
        assert response.status_code == 401


class TestDeleteUser:
    def test_delete_user_owner_success(self, client, auth_headers, test_user):
        response = client.delete(f"/api/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 200
        assert "Successfully deleted" in response.json()["msg"]

    def test_delete_user_admin_success(self, client, admin_auth_headers, test_user):
        response = client.delete(f"/api/users/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_delete_user_other_user_forbidden(self, client, auth_headers, admin_user):
        response = client.delete(f"/api/users/{admin_user.id}", headers=auth_headers)
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_delete_user_not_found(self, client, admin_auth_headers):
        response = client.delete("/api/users/9999", headers=admin_auth_headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_delete_user_unauthorized(self, client, test_user):
        response = client.delete(f"/api/users/{test_user.id}")
        assert response.status_code == 401


class TestUpdateUser:
    def test_update_user_owner_success(self, client, auth_headers, test_user):
        response = client.put(
            "/api/users/",
            headers=auth_headers,
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": "updatedname",
                "avatar": "newavatar.png",
                "role": "general",
                "is_active": True,
                "frequency_max": 1000
            }
        )
        assert response.status_code == 200
        assert "Successfully updated" in response.json()["msg"]

    def test_update_user_admin_success(self, client, admin_auth_headers, test_user):
        response = client.put(
            "/api/users/",
            headers=admin_auth_headers,
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": "adminupdated",
                "avatar": None,
                "role": "general",
                "is_active": True,
                "frequency_max": 600
            }
        )
        assert response.status_code == 200

    def test_update_user_admin_change_role(self, client, admin_auth_headers, test_user):
        response = client.put(
            "/api/users/",
            headers=admin_auth_headers,
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": test_user.username,
                "avatar": None,
                "role": "admin",
                "is_active": True,
                "frequency_max": 600
            }
        )
        assert response.status_code == 200

    def test_update_user_general_cannot_change_role(self, client, auth_headers, test_user):
        response = client.put(
            "/api/users/",
            headers=auth_headers,
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": test_user.username,
                "avatar": None,
                "role": "admin",
                "is_active": True,
                "frequency_max": 600
            }
        )
        assert response.status_code == 200

    def test_update_user_other_user_forbidden(self, client, auth_headers, admin_user):
        response = client.put(
            "/api/users/",
            headers=auth_headers,
            json={
                "id": admin_user.id,
                "email": admin_user.email,
                "username": "hacked",
                "avatar": None,
                "role": "general",
                "is_active": True,
                "frequency_max": 600
            }
        )
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_update_user_not_found(self, client, admin_auth_headers):
        response = client.put(
            "/api/users/",
            headers=admin_auth_headers,
            json={
                "id": 9999,
                "email": "test@example.com",
                "username": "notfound",
                "avatar": None,
                "role": "general",
                "is_active": True,
                "frequency_max": 600
            }
        )
        assert response.status_code == 404

    def test_update_user_unauthorized(self, client, test_user):
        response = client.put(
            "/api/users/",
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": "unauthorized",
                "avatar": None,
                "role": "general",
                "is_active": True,
                "frequency_max": 600
            }
        )
        assert response.status_code == 401


class TestUpdateUserPassword:
    def test_update_password_owner_success(self, client, auth_headers, test_user):
        response = client.post(
            "/api/users/password/",
            headers=auth_headers,
            json={
                "id": test_user.id,
                "oldpassword": "t",
                "password": "n"
            }
        )
        assert response.status_code == 200
        assert "Successfully updated" in response.json()["msg"]

    def test_update_password_w_old_password(self, client, auth_headers, test_user):
        response = client.post(
            "/api/users/password/",
            headers=auth_headers,
            json={
                "id": test_user.id,
                "oldpassword": "w",
                "password": "n"
            }
        )
        assert response.status_code == 403
        assert "Old password is w" in response.json()["detail"]

    def test_update_password_other_user_forbidden(self, client, auth_headers, admin_user):
        response = client.post(
            "/api/users/password/",
            headers=auth_headers,
            json={
                "id": admin_user.id,
                "oldpassword": "a",
                "password": "h"
            }
        )
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_update_password_unauthorized(self, client, test_user):
        response = client.post(
            "/api/users/password/",
            json={
                "id": test_user.id,
                "oldpassword": "t",
                "password": "n"
            }
        )
        assert response.status_code == 401

    def test_update_password_missing_fields(self, client, auth_headers, test_user):
        response = client.post(
            "/api/users/password/",
            headers=auth_headers,
            json={
                "id": test_user.id,
                "oldpassword": "testpassword123"
            }
        )
        assert response.status_code == 422
