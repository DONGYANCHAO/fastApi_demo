import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from sql_app.database import Base, get_db
from sql_app import cruds

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    user_data = type('obj', (object,), {
        'email': 'test@example.com',
        'password': 't'
    })
    return cruds.create_user(db=db_session, user=user_data)


@pytest.fixture(scope="function")
def admin_user(db_session):
    user_data = type('obj', (object,), {
        'email': 'admin@example.com',
        'password': 'a'
    })
    user = cruds.create_user(db=db_session, user=user_data)
    user.role = "admin"
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_token(client, test_user):
    response = client.post(
        "/api/token",
        json={"email": "test@example.com", "password": "t"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    response = client.post(
        "/api/token",
        json={"email": "admin@example.com", "password": "a"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(test_user_token):
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
