# tests/test_auth.py
"""
认证模块单元测试

功能覆盖：
- 生成 JWT Token
- 验证 Token
- 激活校验
- 角色校验
- 登录

覆盖场景：
- 有效 / 无效 / 过期 Token
- 429 限流
- 未激活用户
- 角色拦截
- 登录成败
"""
import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.orm import Session

from sql_app.models import User
from routers.auth import (
    create_access_token,
    get_current_user,
    get_current_active_user,
    role_check,
    TokenData,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    cache
)


class TestCreateAccessToken:
    """JWT Token 生成测试"""
    
    def test_create_access_token_with_expires(self):
        """测试带过期时间的 Token 生成"""
        data = {"sub": "test@example.com"}
        expires = timedelta(minutes=30)
        
        token = create_access_token(data=data, expires_delta=expires)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证 Token 可解码
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload
    
    def test_create_access_token_default_expires(self):
        """测试默认过期时间的 Token 生成"""
        data = {"sub": "test@example.com"}
        
        token = create_access_token(data=data)
        
        assert token is not None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload
    
    def test_create_access_token_custom_data(self):
        """测试包含自定义数据的 Token 生成"""
        data = {
            "sub": "test@example.com",
            "role": "admin",
            "user_id": 123
        }
        expires = timedelta(minutes=30)
        
        token = create_access_token(data=data, expires_delta=expires)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "admin"
        assert payload["user_id"] == 123
    
    def test_create_access_token_expired(self):
        """测试生成已过期的 Token"""
        data = {"sub": "test@example.com"}
        expires = timedelta(minutes=-1)  # 已过期
        
        token = create_access_token(data=data, expires_delta=expires)
        
        # 验证 Token 已过期
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


class TestGetCurrentUser:
    """当前用户获取测试"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, db_session: Session, test_user: User):
        """测试成功获取当前用户"""
        token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(minutes=30)
        )
        
        user = await get_current_user(db_session, token)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session: Session):
        """测试无效 Token"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, "invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, db_session: Session, test_user: User):
        """测试过期 Token"""
        token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(minutes=-1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, db_session: Session):
        """测试 Token 有效但用户不存在"""
        token = create_access_token(
            data={"sub": "nonexistent@example.com"},
            expires_delta=timedelta(minutes=30)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_sub_in_token(self, db_session: Session):
        """测试 Token 中无 sub 字段"""
        token = create_access_token(
            data={"role": "admin"},  # 没有 sub
            expires_delta=timedelta(minutes=30)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_empty_sub(self, db_session: Session):
        """测试 Token 中 sub 为空"""
        token = create_access_token(
            data={"sub": None},
            expires_delta=timedelta(minutes=30)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_malformed_token(self, db_session: Session):
        """测试格式错误的 Token"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, "not.a.token")
        
        assert exc_info.value.status_code == 401


class TestGetCurrentActiveUser:
    """活跃用户验证测试"""
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self, db_session: Session, test_user: User):
        """测试活跃用户验证通过"""
        user = await get_current_active_user(test_user)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self, db_session: Session, inactive_user: User):
        """测试未激活用户被拦截"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(inactive_user)
        
        assert exc_info.value.status_code == 400
        assert "Inactive user" in exc_info.value.detail


class TestRoleCheck:
    """角色权限检查测试"""
    
    def test_role_check_admin_success(self, db_session: Session, admin_user: User):
        """测试管理员角色检查通过"""
        user = role_check(admin_user)
        
        assert user is not None
        assert user.role == "admin"
    
    def test_role_check_general_forbidden(self, db_session: Session, test_user: User):
        """测试普通用户角色检查被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            role_check(test_user)
        
        assert exc_info.value.status_code == 403
        assert "Permission denied" in exc_info.value.detail
    
    def test_role_check_inactive_admin(self, db_session: Session, admin_user: User):
        """测试未激活管理员"""
        admin_user.is_active = False
        
        # role_check 不检查 is_active，只检查 role
        user = role_check(admin_user)
        assert user.role == "admin"


class TestRateLimiting:
    """限流测试"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_not_exceeded(self, db_session: Session, test_user: User):
        """测试未超过限流阈值"""
        # 清除缓存
        cache.clear()
        
        token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(minutes=30)
        )
        
        # 前几次请求应该成功
        for _ in range(5):
            user = await get_current_user(db_session, token)
            assert user is not None
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, db_session: Session, test_user: User):
        """测试超过限流阈值 - 429"""
        # 清除缓存
        cache.clear()
        
        token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(minutes=30)
        )
        
        # 先请求到接近阈值
        for _ in range(test_user.frequency_max):
            await get_current_user(db_session, token)
        
        # 下一次请求应该触发限流
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)
        
        assert exc_info.value.status_code == 429
        assert "Too many requests" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_rate_limit_custom_frequency(self, db_session: Session, test_user: User):
        """测试自定义频率限制"""
        # 清除缓存
        cache.clear()
        
        # 设置较低的频率限制
        test_user.frequency_max = 3
        
        token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(minutes=30)
        )
        
        # 请求 3 次
        for _ in range(3):
            await get_current_user(db_session, token)
        
        # 第 4 次应该被限流
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)
        
        assert exc_info.value.status_code == 429


class TestLogin:
    """登录接口测试"""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """测试成功登录"""
        from sql_app.cruds.users import SECRET_KEY
        
        response = client.post(
            "/api/token",
            json={
                "email": test_user.email,
                "password": "testpassword123" + SECRET_KEY
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == ACCESS_TOKEN_EXPIRE_MINUTES
        assert len(data["access_token"]) > 0
    
    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """测试错误密码登录 - 401"""
        response = client.post(
            "/api/token",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_wrong_email(self, client: TestClient):
        """测试错误邮箱登录 - 401"""
        response = client.post(
            "/api/token",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_empty_credentials(self, client: TestClient):
        """测试空凭据登录 - 422"""
        response = client.post(
            "/api/token",
            json={}
        )
        
        assert response.status_code == 422
    
    def test_login_missing_email(self, client: TestClient):
        """测试缺少邮箱登录 - 422"""
        response = client.post(
            "/api/token",
            json={"password": "password123"}
        )
        
        assert response.status_code == 422
    
    def test_login_missing_password(self, client: TestClient):
        """测试缺少密码登录 - 422"""
        response = client.post(
            "/api/token",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 422
    
    def test_login_inactive_user(self, client: TestClient, inactive_user: User):
        """测试未激活用户登录 - 仍可登录（登录接口不检查激活状态）"""
        from sql_app.cruds.users import SECRET_KEY
        
        response = client.post(
            "/api/token",
            json={
                "email": inactive_user.email,
                "password": "inactivepassword123" + SECRET_KEY
            }
        )
        
        # 登录接口本身不检查 is_active，只是返回 token
        # 实际检查在 get_current_active_user 中
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestTokenValidation:
    """Token 验证测试"""
    
    def test_token_contains_correct_data(self, client: TestClient, test_user: User):
        """测试 Token 包含正确数据"""
        from sql_app.cruds.users import SECRET_KEY
        
        response = client.post(
            "/api/token",
            json={
                "email": test_user.email,
                "password": "testpassword123" + SECRET_KEY
            }
        )
        
        token = response.json()["access_token"]
        
        # 解码验证
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == test_user.email
        assert "exp" in payload
        
        # 验证过期时间是未来时间
        exp_timestamp = payload["exp"]
        current_timestamp = datetime.utcnow().timestamp()
        assert exp_timestamp > current_timestamp
    
    def test_different_users_different_tokens(self, client: TestClient, test_user: User, test_user_2: User):
        """测试不同用户获得不同 Token"""
        from sql_app.cruds.users import SECRET_KEY
        
        # 用户 1 登录
        response1 = client.post(
            "/api/token",
            json={
                "email": test_user.email,
                "password": "testpassword123" + SECRET_KEY
            }
        )
        token1 = response1.json()["access_token"]
        
        # 用户 2 登录
        response2 = client.post(
            "/api/token",
            json={
                "email": test_user_2.email,
                "password": "testpassword456" + SECRET_KEY
            }
        )
        token2 = response2.json()["access_token"]
        
        # 两个 Token 应该不同
        assert token1 != token2
        
        # 解码验证对应用户
        payload1 = jwt.decode(token1, SECRET_KEY, algorithms=[ALGORITHM])
        payload2 = jwt.decode(token2, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload1["sub"] == test_user.email
        assert payload2["sub"] == test_user_2.email


class TestAuthEdgeCases:
    """认证边界条件测试"""
    
    @pytest.mark.asyncio
    async def test_token_with_special_chars_in_email(self, db_session: Session):
        """测试特殊字符邮箱的 Token"""
        email = "user+tag@example.com"
        token = create_access_token(
            data={"sub": email},
            expires_delta=timedelta(minutes=30)
        )
        
        # 只测试 Token 生成，不测试用户查找（因为用户不存在）
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == email
    
    @pytest.mark.asyncio
    async def test_token_with_very_long_email(self, db_session: Session):
        """测试超长邮箱的 Token"""
        email = "a" * 200 + "@example.com"
        token = create_access_token(
            data={"sub": email},
            expires_delta=timedelta(minutes=30)
        )
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == email
    
    def test_wrong_secret_key(self, test_user: User):
        """测试使用错误密钥解码 Token"""
        token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(minutes=30)
        )
        
        # 使用错误的密钥解码
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong_secret_key", algorithms=[ALGORITHM])
    
    def test_wrong_algorithm(self, test_user: User):
        """测试使用错误算法解码 Token"""
        token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(minutes=30)
        )
        
        # 使用错误的算法解码
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, SECRET_KEY, algorithms=["HS512"])


class TestCacheBehavior:
    """缓存行为测试"""
    
    def test_cache_isolation_between_tests(self):
        """测试缓存测试隔离"""
        cache.clear()
        
        # 设置一些缓存值
        cache.set("key1", 1)
        assert cache.get("key1") == 1
        
        # 清除缓存
        cache.clear()
        assert cache.get("key1") is None
