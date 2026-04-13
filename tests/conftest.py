# tests/conftest.py
"""
共享 fixture 配置
提供内存数据库、测试客户端、测试用户、认证重写等 fixture
"""
import pytest
from datetime import datetime, timedelta
from typing import Generator, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from fastapi import Depends

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_app.database import Base, get_db
from sql_app.models import User
from sql_app.schemas import schemas_user
from sql_app import cruds
from main import app
from routers.auth import (
    create_access_token,
    get_current_user,
    get_current_active_user,
    role_check,
    SECRET_KEY,
    ALGORITHM
)

# 内存数据库 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# 创建内存数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

# 创建测试会话工厂
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """
    创建数据库引擎 fixture
    在整个测试会话期间只创建一次
    """
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    创建数据库会话 fixture
    每个测试函数独立，确保测试隔离性
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    创建测试客户端 fixture
    重写 get_db 依赖，使用内存数据库会话
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """
    创建普通测试用户 fixture
    """
    user_data = schemas_user.UserCreate(
        email="test@example.com",
        password="testpassword123"
    )
    user = cruds.create_user(db_session, user_data)
    return user


@pytest.fixture(scope="function")
def test_user_2(db_session: Session) -> User:
    """
    创建第二个普通测试用户 fixture
    用于测试用户间权限隔离
    """
    user_data = schemas_user.UserCreate(
        email="test2@example.com",
        password="testpassword456"
    )
    user = cruds.create_user(db_session, user_data)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session: Session) -> User:
    """
    创建管理员测试用户 fixture
    """
    user_data = schemas_user.UserCreate(
        email="admin@example.com",
        password="adminpassword123"
    )
    user = cruds.create_user(db_session, user_data)
    user.role = "admin"
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def inactive_user(db_session: Session) -> User:
    """
    创建未激活测试用户 fixture
    用于测试激活状态验证
    """
    user_data = schemas_user.UserCreate(
        email="inactive@example.com",
        password="inactivepassword123"
    )
    user = cruds.create_user(db_session, user_data)
    user.is_active = False
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def user_token(test_user: User) -> str:
    """
    生成普通用户 JWT token fixture
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=access_token_expires
    )
    return access_token


@pytest.fixture(scope="function")
def admin_token(admin_user: User) -> str:
    """
    生成管理员 JWT token fixture
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": admin_user.email},
        expires_delta=access_token_expires
    )
    return access_token


@pytest.fixture(scope="function")
def inactive_user_token(inactive_user: User) -> str:
    """
    生成未激活用户 JWT token fixture
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": inactive_user.email},
        expires_delta=access_token_expires
    )
    return access_token


@pytest.fixture(scope="function")
def expired_token(test_user: User) -> str:
    """
    生成过期 JWT token fixture
    """
    access_token_expires = timedelta(minutes=-1)  # 已过期
    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=access_token_expires
    )
    return access_token


@pytest.fixture(scope="function")
def user_auth_headers(user_token: str) -> Dict[str, str]:
    """
    普通用户认证请求头 fixture
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(admin_token: str) -> Dict[str, str]:
    """
    管理员认证请求头 fixture
    """
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def inactive_user_auth_headers(inactive_user_token: str) -> Dict[str, str]:
    """
    未激活用户认证请求头 fixture
    """
    return {"Authorization": f"Bearer {inactive_user_token}"}


@pytest.fixture(scope="function")
def multiple_users(db_session: Session) -> list:
    """
    创建多个测试用户 fixture
    用于测试分页功能
    """
    users = []
    for i in range(15):
        user_data = schemas_user.UserCreate(
            email=f"user{i}@example.com",
            password=f"password{i}"
        )
        user = cruds.create_user(db_session, user_data)
        users.append(user)
    return users
