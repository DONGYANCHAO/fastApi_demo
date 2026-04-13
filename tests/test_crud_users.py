# tests/test_crud_users.py
"""
用户 CRUD 单元测试
测试范围：
- 查询用户 / 邮箱查询 / 列表查询
- 登录验证
- 创建 / 更新 / 删除 / 修改密码
- 密码哈希 / 密码验证

覆盖场景：
- 正常流程
- 空库查询
- 分页功能
- 不存在用户
- 错误密码
- 密码全流程
"""
import pytest
from sqlalchemy.orm import Session

from sql_app import cruds, models
from sql_app.schemas import schemas_user
from sql_app.cruds.users import (
    get_password_hash,
    verify_password,
    get_user,
    get_user_by_email,
    get_user_by_login,
    get_users,
    create_user,
    delete_user,
    update_user,
    update_user_password
)


class TestPasswordHash:
    """密码哈希相关测试"""
    
    def test_get_password_hash_generates_different_hashes(self):
        """测试相同密码生成不同哈希值（由于盐值）"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert len(hash1) > 0
        assert len(hash2) > 0
    
    def test_verify_password_correct(self):
        """测试正确密码验证通过"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """测试错误密码验证失败"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """测试空密码验证失败"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """测试密码大小写敏感"""
        password = "TestPassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TESTPASSWORD123", hashed) is False


class TestGetUser:
    """查询用户测试"""
    
    def test_get_user_by_id_success(self, db_session: Session, test_user: models.User):
        """测试通过 ID 成功获取用户"""
        user = get_user(db_session, test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.username == test_user.username
    
    def test_get_user_by_id_not_found(self, db_session: Session):
        """测试获取不存在的用户返回 None"""
        user = get_user(db_session, 99999)
        
        assert user is None
    
    def test_get_user_by_id_negative(self, db_session: Session):
        """测试使用负数 ID 查询"""
        user = get_user(db_session, -1)
        
        assert user is None
    
    def test_get_user_by_id_zero(self, db_session: Session):
        """测试使用 0 ID 查询"""
        user = get_user(db_session, 0)
        
        assert user is None


class TestGetUserByEmail:
    """通过邮箱查询用户测试"""
    
    def test_get_user_by_email_success(self, db_session: Session, test_user: models.User):
        """测试通过邮箱成功获取用户"""
        user = get_user_by_email(db_session, test_user.email)
        
        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id
    
    def test_get_user_by_email_not_found(self, db_session: Session):
        """测试获取不存在的邮箱返回 None"""
        user = get_user_by_email(db_session, "nonexistent@example.com")
        
        assert user is None
    
    def test_get_user_by_email_empty(self, db_session: Session):
        """测试空邮箱查询"""
        user = get_user_by_email(db_session, "")
        
        assert user is None
    
    def test_get_user_by_email_invalid_format(self, db_session: Session):
        """测试无效邮箱格式查询"""
        user = get_user_by_email(db_session, "invalid-email")
        
        assert user is None
    
    def test_get_user_by_email_case_sensitive(self, db_session: Session, test_user: models.User):
        """测试邮箱大小写敏感"""
        user = get_user_by_email(db_session, test_user.email.upper())
        
        assert user is None


class TestGetUserByLogin:
    """登录验证测试"""
    
    def test_get_user_by_login_success(self, db_session: Session, test_user: models.User):
        """测试正确邮箱密码登录成功"""
        from sql_app.cruds.users import SECRET_KEY
        
        user = get_user_by_login(db_session, test_user.email, "testpassword123" + SECRET_KEY)
        
        assert user is not False
        assert user.email == test_user.email
    
    def test_get_user_by_login_wrong_password(self, db_session: Session, test_user: models.User):
        """测试错误密码登录失败"""
        user = get_user_by_login(db_session, test_user.email, "wrongpassword")
        
        assert user is False
    
    def test_get_user_by_login_wrong_email(self, db_session: Session):
        """测试错误邮箱登录失败"""
        user = get_user_by_login(db_session, "wrong@example.com", "anypassword")
        
        assert user is False
    
    def test_get_user_by_login_empty_password(self, db_session: Session, test_user: models.User):
        """测试空密码登录失败"""
        user = get_user_by_login(db_session, test_user.email, "")
        
        assert user is False


class TestGetUsers:
    """获取用户列表测试"""
    
    def test_get_users_empty_db(self, db_session: Session):
        """测试空数据库返回空列表"""
        users = get_users(db_session)
        
        assert users == []
    
    def test_get_users_single_user(self, db_session: Session, test_user: models.User):
        """测试获取单个用户"""
        users = get_users(db_session)
        
        assert len(users) == 1
        assert users[0].id == test_user.id
    
    def test_get_users_multiple(self, db_session: Session, multiple_users: list):
        """测试获取多个用户"""
        users = get_users(db_session)
        
        assert len(users) == 15
    
    def test_get_users_with_skip(self, db_session: Session, multiple_users: list):
        """测试 skip 分页"""
        users = get_users(db_session, skip=5)
        
        assert len(users) == 10
    
    def test_get_users_with_limit(self, db_session: Session, multiple_users: list):
        """测试 limit 分页"""
        users = get_users(db_session, limit=5)
        
        assert len(users) == 5
    
    def test_get_users_with_skip_and_limit(self, db_session: Session, multiple_users: list):
        """测试 skip 和 limit 组合分页"""
        users = get_users(db_session, skip=5, limit=5)
        
        assert len(users) == 5
    
    def test_get_users_skip_exceed_total(self, db_session: Session, test_user: models.User):
        """测试 skip 超过总数返回空列表"""
        users = get_users(db_session, skip=100)
        
        assert users == []
    
    def test_get_users_negative_skip(self, db_session: Session, test_user: models.User):
        """测试负数 skip"""
        users = get_users(db_session, skip=-1)
        
        assert len(users) >= 0
    
    def test_get_users_zero_limit(self, db_session: Session, multiple_users: list):
        """测试 limit 为 0"""
        users = get_users(db_session, limit=0)
        
        assert users == []


class TestCreateUser:
    """创建用户测试"""
    
    def test_create_user_success(self, db_session: Session):
        """测试成功创建用户"""
        user_data = schemas_user.UserCreate(
            email="newuser@example.com",
            password="newpassword123"
        )
        
        user = create_user(db_session, user_data)
        
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.role == "general"
        assert user.is_active is True
        assert user.hashed_password is not None
        assert user.hashed_password != "newpassword123"
    
    def test_create_user_username_from_email(self, db_session: Session):
        """测试用户名从邮箱提取"""
        user_data = schemas_user.UserCreate(
            email="test.name@example.com",
            password="password123"
        )
        
        user = create_user(db_session, user_data)
        
        assert user.username == "test.name"
    
    def test_create_user_email_without_at(self, db_session: Session):
        """测试无 @ 符号的邮箱作为用户名"""
        user_data = schemas_user.UserCreate(
            email="username",
            password="password123"
        )
        
        user = create_user(db_session, user_data)
        
        assert user.username == "username"
    
    def test_create_user_duplicate_email(self, db_session: Session, test_user: models.User):
        """测试重复邮箱创建失败"""
        from sqlalchemy.exc import IntegrityError
        
        user_data = schemas_user.UserCreate(
            email=test_user.email,
            password="anotherpassword"
        )
        
        with pytest.raises(IntegrityError):
            create_user(db_session, user_data)
            db_session.commit()
        db_session.rollback()


class TestDeleteUser:
    """删除用户测试"""
    
    def test_delete_user_success(self, db_session: Session, test_user: models.User):
        """测试成功删除用户"""
        result = delete_user(db_session, test_user.id)
        
        assert result == 1
        assert get_user(db_session, test_user.id) is None
    
    def test_delete_user_not_found(self, db_session: Session):
        """测试删除不存在的用户"""
        result = delete_user(db_session, 99999)
        
        assert result == 0
    
    def test_delete_user_already_deleted(self, db_session: Session, test_user: models.User):
        """测试重复删除同一用户"""
        delete_user(db_session, test_user.id)
        result = delete_user(db_session, test_user.id)
        
        assert result == 0
    
    def test_delete_user_negative_id(self, db_session: Session):
        """测试删除负数 ID 用户"""
        result = delete_user(db_session, -1)
        
        assert result == 0


class TestUpdateUser:
    """更新用户测试"""
    
    def test_update_user_success(self, db_session: Session, test_user: models.User):
        """测试成功更新用户"""
        update_data = schemas_user.User(
            id=test_user.id,
            email=test_user.email,
            username="updated_username",
            avatar="http://example.com/avatar.jpg",
            role=test_user.role,
            is_active=test_user.is_active,
            frequency_max=test_user.frequency_max
        )
        
        result = update_user(db_session, update_data)
        
        assert result == 1
        
        updated_user = get_user(db_session, test_user.id)
        assert updated_user.username == "updated_username"
        assert updated_user.avatar == "http://example.com/avatar.jpg"
    
    def test_update_user_not_found(self, db_session: Session):
        """测试更新不存在的用户"""
        update_data = schemas_user.User(
            id=99999,
            email="test@example.com",
            username="test",
            avatar=None,
            role="general",
            is_active=True,
            frequency_max=600
        )
        
        result = update_user(db_session, update_data)
        
        assert result == 0
    
    def test_update_user_partial(self, db_session: Session, test_user: models.User):
        """测试部分字段更新"""
        original_username = test_user.username
        update_data = schemas_user.User(
            id=test_user.id,
            email=test_user.email,
            username=original_username,
            avatar=test_user.avatar,
            role="admin",
            is_active=test_user.is_active,
            frequency_max=1000
        )
        
        result = update_user(db_session, update_data)
        
        assert result == 1
        
        updated_user = get_user(db_session, test_user.id)
        assert updated_user.role == "admin"
        assert updated_user.frequency_max == 1000


class TestUpdateUserPassword:
    """修改密码测试"""
    
    def test_update_user_password_success(self, db_session: Session, test_user: models.User):
        """测试成功修改密码"""
        from sql_app.cruds.users import SECRET_KEY
        
        password_data = schemas_user.UserPassWord(
            id=test_user.id,
            oldpassword="testpassword123" + SECRET_KEY,
            password="newpassword456"
        )
        
        result = update_user_password(db_session, password_data)
        
        assert result == 1
        
        # 验证新密码可以登录
        user = get_user_by_login(db_session, test_user.email, "newpassword456" + SECRET_KEY)
        assert user is not False
    
    def test_update_user_password_wrong_old_password(self, db_session: Session, test_user: models.User):
        """测试错误旧密码修改失败"""
        password_data = schemas_user.UserPassWord(
            id=test_user.id,
            oldpassword="wrongpassword",
            password="newpassword456"
        )
        
        result = update_user_password(db_session, password_data)
        
        assert result is False
    
    def test_update_user_password_user_not_found(self, db_session: Session):
        """测试修改不存在用户的密码"""
        password_data = schemas_user.UserPassWord(
            id=99999,
            oldpassword="oldpassword",
            password="newpassword456"
        )
        
        result = update_user_password(db_session, password_data)
        
        assert result is False
    
    def test_update_user_password_same_password(self, db_session: Session, test_user: models.User):
        """测试新旧密码相同"""
        from sql_app.cruds.users import SECRET_KEY
        
        password_data = schemas_user.UserPassWord(
            id=test_user.id,
            oldpassword="testpassword123" + SECRET_KEY,
            password="testpassword123" + SECRET_KEY
        )
        
        result = update_user_password(db_session, password_data)
        
        assert result == 1


class TestIntegration:
    """集成测试 - 完整用户生命周期"""
    
    def test_user_lifecycle(self, db_session: Session):
        """测试用户完整生命周期"""
        from sql_app.cruds.users import SECRET_KEY
        
        # 1. 创建用户
        user_data = schemas_user.UserCreate(
            email="lifecycle@example.com",
            password="lifecycle123"
        )
        user = create_user(db_session, user_data)
        assert user is not None
        user_id = user.id
        
        # 2. 查询用户
        found_user = get_user(db_session, user_id)
        assert found_user is not None
        assert found_user.email == "lifecycle@example.com"
        
        # 3. 登录验证
        logged_user = get_user_by_login(db_session, "lifecycle@example.com", "lifecycle123" + SECRET_KEY)
        assert logged_user is not False
        
        # 4. 更新用户信息
        update_data = schemas_user.User(
            id=user_id,
            email="lifecycle@example.com",
            username="lifecycle_updated",
            avatar=None,
            role="general",
            is_active=True,
            frequency_max=600
        )
        result = update_user(db_session, update_data)
        assert result == 1
        
        # 5. 修改密码
        password_data = schemas_user.UserPassWord(
            id=user_id,
            oldpassword="lifecycle123" + SECRET_KEY,
            password="newlifecycle456"
        )
        result = update_user_password(db_session, password_data)
        assert result == 1
        
        # 6. 使用新密码登录
        logged_user = get_user_by_login(db_session, "lifecycle@example.com", "newlifecycle456" + SECRET_KEY)
        assert logged_user is not False
        
        # 7. 旧密码无法登录
        old_login = get_user_by_login(db_session, "lifecycle@example.com", "lifecycle123" + SECRET_KEY)
        assert old_login is False
        
        # 8. 删除用户
        result = delete_user(db_session, user_id)
        assert result == 1
        
        # 9. 确认用户已删除
        deleted_user = get_user(db_session, user_id)
        assert deleted_user is None
