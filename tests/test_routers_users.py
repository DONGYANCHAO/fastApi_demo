# tests/test_routers_users.py
"""
用户路由集成测试

接口覆盖：
- POST /api/users/ - 创建用户
- GET /api/users/ - 获取所有用户（需管理员权限）
- GET /api/users/me - 获取本人信息
- GET /api/users/{user_id} - 根据ID查询用户
- DELETE /api/users/{user_id} - 删除用户
- PUT /api/users/ - 更新用户
- POST /api/users/password/ - 修改密码

权限测试：
- 公开接口
- 仅管理员
- 仅本人
- 仅本人 + 管理员

状态码测试：
200/400/401/403/404/422
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sql_app.models import User


class TestCreateUser:
    """创建用户接口测试"""
    
    def test_create_user_success(self, client: TestClient):
        """测试成功创建用户 - 200"""
        response = client.post(
            "/api/users/",
            json={"email": "newuser@example.com", "password": "newpassword123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["role"] == "general"
        assert data["is_active"] is True
        assert "id" in data
    
    def test_create_user_duplicate_email(self, client: TestClient, test_user: User):
        """测试重复邮箱创建 - 400"""
        response = client.post(
            "/api/users/",
            json={"email": test_user.email, "password": "password123"}
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_create_user_invalid_email_format(self, client: TestClient):
        """测试无效邮箱格式 - 422"""
        response = client.post(
            "/api/users/",
            json={"email": "invalid-email", "password": "password123"}
        )
        
        assert response.status_code == 422
    
    def test_create_user_missing_email(self, client: TestClient):
        """测试缺少邮箱 - 422"""
        response = client.post(
            "/api/users/",
            json={"password": "password123"}
        )
        
        assert response.status_code == 422
    
    def test_create_user_missing_password(self, client: TestClient):
        """测试缺少密码 - 422"""
        response = client.post(
            "/api/users/",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 422
    
    def test_create_user_empty_password(self, client: TestClient):
        """测试空密码 - 422"""
        response = client.post(
            "/api/users/",
            json={"email": "test@example.com", "password": ""}
        )
        
        assert response.status_code == 422
    
    def test_create_user_empty_email(self, client: TestClient):
        """测试空邮箱 - 422"""
        response = client.post(
            "/api/users/",
            json={"email": "", "password": "password123"}
        )
        
        assert response.status_code == 422


class TestGetUsers:
    """获取所有用户接口测试 - 需管理员权限"""
    
    def test_get_users_admin_success(self, client: TestClient, admin_auth_headers: dict, multiple_users: list):
        """测试管理员获取所有用户 - 200"""
        response = client.get("/api/users/", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 15
    
    def test_get_users_general_forbidden(self, client: TestClient, user_auth_headers: dict):
        """测试普通用户获取所有用户 - 403"""
        response = client.get("/api/users/", headers=user_auth_headers)
        
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]
    
    def test_get_users_no_auth(self, client: TestClient):
        """测试未认证获取所有用户 - 401"""
        response = client.get("/api/users/")
        
        assert response.status_code == 401
    
    def test_get_users_with_pagination(self, client: TestClient, admin_auth_headers: dict, multiple_users: list):
        """测试分页获取用户 - 200"""
        response = client.get("/api/users/?skip=5&limit=5", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_get_users_empty_db(self, client: TestClient, admin_auth_headers: dict):
        """测试空数据库获取用户 - 200"""
        response = client.get("/api/users/", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestGetUserMe:
    """获取本人信息接口测试"""
    
    def test_get_user_me_success(self, client: TestClient, user_auth_headers: dict, test_user: User):
        """测试获取本人信息 - 200"""
        response = client.get("/api/users/me", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    def test_get_user_me_no_auth(self, client: TestClient):
        """测试未认证获取本人信息 - 401"""
        response = client.get("/api/users/me")
        
        assert response.status_code == 401
    
    def test_get_user_me_invalid_token(self, client: TestClient):
        """测试无效 token 获取本人信息 - 401"""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401


class TestGetUserById:
    """根据ID查询用户接口测试"""
    
    def test_get_user_by_id_self_success(self, client: TestClient, user_auth_headers: dict, test_user: User):
        """测试用户查询自己信息 - 200"""
        response = client.get(f"/api/users/{test_user.id}", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
    
    def test_get_user_by_id_admin_can_query_any(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """测试管理员可查询任意用户 - 200"""
        response = client.get(f"/api/users/{test_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
    
    def test_get_user_by_id_general_cannot_query_others(self, client: TestClient, user_auth_headers: dict, test_user_2: User):
        """测试普通用户禁止查询他人信息 - 403"""
        response = client.get(f"/api/users/{test_user_2.id}", headers=user_auth_headers)
        
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]
    
    def test_get_user_by_id_not_found(self, client: TestClient, user_auth_headers: dict):
        """测试查询不存在用户 - 404"""
        response = client.get("/api/users/99999", headers=user_auth_headers)
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_get_user_by_id_no_auth(self, client: TestClient, test_user: User):
        """测试未认证查询用户 - 401"""
        response = client.get(f"/api/users/{test_user.id}")
        
        assert response.status_code == 401
    
    def test_get_user_by_id_negative_id(self, client: TestClient, user_auth_headers: dict):
        """测试负数 ID 查询 - 404"""
        response = client.get("/api/users/-1", headers=user_auth_headers)
        
        assert response.status_code == 404


class TestDeleteUser:
    """删除用户接口测试"""
    
    def test_delete_user_self_success(self, client: TestClient, db_session: Session, user_auth_headers: dict, test_user: User):
        """测试用户删除自己 - 200"""
        response = client.delete(f"/api/users/{test_user.id}", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully deleted" in data["msg"]
    
    def test_delete_user_admin_can_delete_any(self, client: TestClient, db_session: Session, admin_auth_headers: dict, test_user: User):
        """测试管理员可删除任意用户 - 200"""
        response = client.delete(f"/api/users/{test_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully deleted" in data["msg"]
    
    def test_delete_user_general_cannot_delete_others(self, client: TestClient, user_auth_headers: dict, test_user_2: User):
        """测试普通用户禁止删除他人 - 403"""
        response = client.delete(f"/api/users/{test_user_2.id}", headers=user_auth_headers)
        
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]
    
    def test_delete_user_not_found(self, client: TestClient, user_auth_headers: dict):
        """测试删除不存在用户 - 404"""
        response = client.delete("/api/users/99999", headers=user_auth_headers)
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_delete_user_no_auth(self, client: TestClient, test_user: User):
        """测试未认证删除用户 - 401"""
        response = client.delete(f"/api/users/{test_user.id}")
        
        assert response.status_code == 401


class TestUpdateUser:
    """更新用户接口测试"""
    
    def test_update_user_self_success(self, client: TestClient, user_auth_headers: dict, test_user: User):
        """测试用户更新自己信息 - 200"""
        response = client.put(
            "/api/users/",
            headers=user_auth_headers,
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": "updated_username",
                "avatar": "http://example.com/avatar.jpg",
                "role": test_user.role,
                "is_active": test_user.is_active,
                "frequency_max": test_user.frequency_max
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully updated" in data["msg"]
    
    def test_update_user_admin_can_update_any(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """测试管理员可更新任意用户 - 200"""
        response = client.put(
            "/api/users/",
            headers=admin_auth_headers,
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": "admin_updated",
                "avatar": None,
                "role": "admin",
                "is_active": test_user.is_active,
                "frequency_max": 1000
            }
        )
        
        assert response.status_code == 200
    
    def test_update_user_general_cannot_update_others(self, client: TestClient, user_auth_headers: dict, test_user_2: User):
        """测试普通用户禁止更新他人信息 - 403"""
        response = client.put(
            "/api/users/",
            headers=user_auth_headers,
            json={
                "id": test_user_2.id,
                "email": test_user_2.email,
                "username": "hacked",
                "avatar": None,
                "role": test_user_2.role,
                "is_active": test_user_2.is_active,
                "frequency_max": test_user_2.frequency_max
            }
        )
        
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]
    
    def test_update_user_not_found(self, client: TestClient, user_auth_headers: dict):
        """测试更新不存在用户 - 404"""
        response = client.put(
            "/api/users/",
            headers=user_auth_headers,
            json={
                "id": 99999,
                "email": "test@example.com",
                "username": "test",
                "avatar": None,
                "role": "general",
                "is_active": True,
                "frequency_max": 600
            }
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_update_user_general_cannot_change_role(self, client: TestClient, db_session: Session, user_auth_headers: dict, test_user: User):
        """测试普通用户尝试修改角色被重置为 general"""
        response = client.put(
            "/api/users/",
            headers=user_auth_headers,
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": test_user.username,
                "avatar": None,
                "role": "admin",
                "is_active": test_user.is_active,
                "frequency_max": test_user.frequency_max
            }
        )
        
        assert response.status_code == 200
        
        # 验证角色未被修改为 admin
        from sql_app.cruds import get_user
        updated_user = get_user(db_session, test_user.id)
        assert updated_user.role == "general"
    
    def test_update_user_no_auth(self, client: TestClient, test_user: User):
        """测试未认证更新用户 - 401"""
        response = client.put(
            "/api/users/",
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": "updated",
                "avatar": None,
                "role": test_user.role,
                "is_active": test_user.is_active,
                "frequency_max": test_user.frequency_max
            }
        )
        
        assert response.status_code == 401


class TestUpdateUserPassword:
    """修改密码接口测试"""
    
    def test_update_password_success(self, client: TestClient, db_session: Session, user_auth_headers: dict, test_user: User):
        """测试成功修改密码 - 200"""
        from sql_app.cruds.users import SECRET_KEY
        
        response = client.post(
            "/api/users/password/",
            headers=user_auth_headers,
            json={
                "id": test_user.id,
                "oldpassword": "testpassword123" + SECRET_KEY,
                "password": "newpassword456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully updated" in data["msg"]
    
    def test_update_password_wrong_old_password(self, client: TestClient, user_auth_headers: dict, test_user: User):
        """测试错误旧密码 - 403"""
        response = client.post(
            "/api/users/password/",
            headers=user_auth_headers,
            json={
                "id": test_user.id,
                "oldpassword": "wrongpassword",
                "password": "newpassword456"
            }
        )
        
        assert response.status_code == 403
        assert "Old password is wrong" in response.json()["detail"]
    
    def test_update_password_cannot_change_others(self, client: TestClient, user_auth_headers: dict, test_user_2: User):
        """测试禁止修改他人密码 - 403"""
        from sql_app.cruds.users import SECRET_KEY
        
        response = client.post(
            "/api/users/password/",
            headers=user_auth_headers,
            json={
                "id": test_user_2.id,
                "oldpassword": "testpassword456" + SECRET_KEY,
                "password": "hackedpassword"
            }
        )
        
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]
    
    def test_update_password_no_auth(self, client: TestClient, test_user: User):
        """测试未认证修改密码 - 401"""
        response = client.post(
            "/api/users/password/",
            json={
                "id": test_user.id,
                "oldpassword": "oldpass",
                "password": "newpass"
            }
        )
        
        assert response.status_code == 401
    
    def test_update_password_missing_fields(self, client: TestClient, user_auth_headers: dict):
        """测试缺少必填字段 - 422"""
        response = client.post(
            "/api/users/password/",
            headers=user_auth_headers,
            json={"id": 1}
        )
        
        assert response.status_code == 422


class TestEdgeCases:
    """边界条件测试"""
    
    def test_create_user_very_long_username(self, client: TestClient):
        """测试超长用户名"""
        long_email = "a" * 200 + "@example.com"
        response = client.post(
            "/api/users/",
            json={"email": long_email, "password": "password123"}
        )
        
        # SQLite 可以存储，但可能截断
        assert response.status_code in [200, 422]
    
    def test_create_user_special_chars_in_email(self, client: TestClient):
        """测试特殊字符邮箱"""
        response = client.post(
            "/api/users/",
            json={"email": "test+label@example.com", "password": "password123"}
        )
        
        assert response.status_code == 200
    
    def test_update_user_invalid_json(self, client: TestClient, user_auth_headers: dict):
        """测试无效 JSON 格式"""
        response = client.put(
            "/api/users/",
            headers={**user_auth_headers, "Content-Type": "application/json"},
            data="invalid json"
        )
        
        assert response.status_code == 422
    
    def test_get_users_invalid_skip_type(self, client: TestClient, admin_auth_headers: dict):
        """测试无效 skip 参数类型"""
        response = client.get("/api/users/?skip=abc", headers=admin_auth_headers)
        
        assert response.status_code == 422
    
    def test_get_users_invalid_limit_type(self, client: TestClient, admin_auth_headers: dict):
        """测试无效 limit 参数类型"""
        response = client.get("/api/users/?limit=abc", headers=admin_auth_headers)
        
        assert response.status_code == 422


class TestPermissionMatrix:
    """权限矩阵测试"""
    
    def test_permission_matrix_summary(self, client: TestClient, db_session: Session, 
                                        admin_user: User, test_user: User, test_user_2: User,
                                        admin_auth_headers: dict, user_auth_headers: dict):
        """测试权限矩阵汇总"""
        
        # 1. 管理员可以获取所有用户列表
        response = client.get("/api/users/", headers=admin_auth_headers)
        assert response.status_code == 200
        
        # 2. 普通用户不能获取所有用户列表
        response = client.get("/api/users/", headers=user_auth_headers)
        assert response.status_code == 403
        
        # 3. 管理员可以查询任意用户信息
        response = client.get(f"/api/users/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        response = client.get(f"/api/users/{test_user_2.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        
        # 4. 普通用户只能查询自己
        response = client.get(f"/api/users/{test_user.id}", headers=user_auth_headers)
        assert response.status_code == 200
        response = client.get(f"/api/users/{test_user_2.id}", headers=user_auth_headers)
        assert response.status_code == 403
        
        # 5. 管理员可以删除任意用户
        new_user_data = {"email": "deletetest@example.com", "password": "password123"}
        client.post("/api/users/", json=new_user_data)
        new_user = db_session.query(User).filter(User.email == "deletetest@example.com").first()
        response = client.delete(f"/api/users/{new_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        
        # 6. 普通用户只能删除自己
        response = client.delete(f"/api/users/{test_user_2.id}", headers=user_auth_headers)
        assert response.status_code == 403
        
        # 7. 管理员可以更新任意用户
        response = client.put(
            "/api/users/",
            headers=admin_auth_headers,
            json={
                "id": test_user.id,
                "email": test_user.email,
                "username": "admin_can_update",
                "avatar": None,
                "role": "admin",
                "is_active": test_user.is_active,
                "frequency_max": test_user.frequency_max
            }
        )
        assert response.status_code == 200
        
        # 8. 普通用户只能更新自己
        response = client.put(
            "/api/users/",
            headers=user_auth_headers,
            json={
                "id": test_user_2.id,
                "email": test_user_2.email,
                "username": "hacked",
                "avatar": None,
                "role": test_user_2.role,
                "is_active": test_user_2.is_active,
                "frequency_max": test_user_2.frequency_max
            }
        )
        assert response.status_code == 403
        
        # 9. 用户只能修改自己的密码
        response = client.post(
            "/api/users/password/",
            headers=user_auth_headers,
            json={
                "id": test_user_2.id,
                "oldpassword": "any",
                "password": "newpass"
            }
        )
        assert response.status_code == 403
