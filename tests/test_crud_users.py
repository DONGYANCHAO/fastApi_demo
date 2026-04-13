import pytest
from sql_app import cruds


class TestPasswordOperations:
    def test_get_password_hash(self):
        password = "testpassword123"
        hashed = cruds.get_password_hash(password + cruds.SECRET_KEY)
        assert hashed is not None
        assert hashed != password

    def test_verify_password_success(self):
        password = "testpassword123" + cruds.SECRET_KEY
        hashed = cruds.get_password_hash(password)
        assert cruds.verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        password = "testpassword123" + cruds.SECRET_KEY
        wrong_password = "w" + cruds.SECRET_KEY
        hashed = cruds.get_password_hash(password)
        assert cruds.verify_password(wrong_password, hashed) is False

    def test_password_hash_unique(self):
        password = "samepassword" + cruds.SECRET_KEY
        hash1 = cruds.get_password_hash(password)
        hash2 = cruds.get_password_hash(password)
        assert hash1 != hash2


class TestGetUser:
    def test_get_user_success(self, db_session, test_user):
        user = cruds.get_user(db_session, user_id=test_user.id)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == "test@example.com"

    def test_get_user_not_found(self, db_session):
        user = cruds.get_user(db_session, user_id=9999)
        assert user is None

    def test_get_user_negative_id(self, db_session):
        user = cruds.get_user(db_session, user_id=-1)
        assert user is None

    def test_get_user_empty_db(self, db_session):
        user = cruds.get_user(db_session, user_id=1)
        assert user is None


class TestGetUserByEmail:
    def test_get_user_by_email_success(self, db_session, test_user):
        user = cruds.get_user_by_email(db_session, email="test@example.com")
        assert user is not None
        assert user.email == "test@example.com"

    def test_get_user_by_email_not_found(self, db_session):
        user = cruds.get_user_by_email(db_session, email="nonexistent@example.com")
        assert user is None

    def test_get_user_by_email_empty_string(self, db_session):
        user = cruds.get_user_by_email(db_session, email="")
        assert user is None

    def test_get_user_by_email_case_sensitive(self, db_session, test_user):
        user = cruds.get_user_by_email(db_session, email="TEST@EXAMPLE.COM")
        assert user is None


class TestGetUserByLogin:
    def test_get_user_by_login_success(self, db_session, test_user):
        user = cruds.get_user_by_login(db_session, email="test@example.com", password="t")
        assert user is not False
        assert user.email == "test@example.com"

    def test_get_user_by_login_wrong_password(self, db_session, test_user):
        result = cruds.get_user_by_login(db_session, email="test@example.com", password="wrong")
        assert result is False

    def test_get_user_by_login_wrong_email(self, db_session):
        result = cruds.get_user_by_login(db_session, email="wrong@example.com", password="t")
        assert result is False

    def test_get_user_by_login_empty_password(self, db_session, test_user):
        result = cruds.get_user_by_login(db_session, email="test@example.com", password="")
        assert result is False

    def test_get_user_by_login_empty_email(self, db_session):
        result = cruds.get_user_by_login(db_session, email="", password="pwd")
        assert result is False


class TestGetUsers:
    def test_get_users_all(self, db_session):
        for i in range(5):
            user_data = type('obj', (object,), {
                'email': f'user{i}@example.com',
                'password': 'p'
            })
            cruds.create_user(db_session, user=user_data)

        users = cruds.get_users(db_session)
        assert len(users) == 5

    def test_get_users_pagination(self, db_session):
        for i in range(10):
            user_data = type('obj', (object,), {
                'email': f'user{i}@example.com',
                'password': 'p'
            })
            cruds.create_user(db_session, user=user_data)

        users_page1 = cruds.get_users(db_session, skip=0, limit=5)
        users_page2 = cruds.get_users(db_session, skip=5, limit=5)
        assert len(users_page1) == 5
        assert len(users_page2) == 5
        assert users_page1[0].email != users_page2[0].email

    def test_get_users_empty_db(self, db_session):
        users = cruds.get_users(db_session)
        assert len(users) == 0

    def test_get_users_limit_zero(self, db_session, test_user):
        users = cruds.get_users(db_session, limit=0)
        assert len(users) == 0

    def test_get_users_skip_larger_than_total(self, db_session, test_user):
        users = cruds.get_users(db_session, skip=100)
        assert len(users) == 0


class TestCreateUser:
    def test_create_user_success(self, db_session):
        user_data = type('obj', (object,), {
            'email': 'newuser@example.com',
            'password': 'newp'
        })
        user = cruds.create_user(db_session, user=user_data)
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.hashed_password is not None
        assert user.role == "general"
        assert user.is_active is True

    def test_create_user_username_from_email(self, db_session):
        user_data = type('obj', (object,), {
            'email': 'noatsign',
            'password': 'p'
        })
        user = cruds.create_user(db_session, user=user_data)
        assert user.username == "noatsign"

    def test_create_user_long_email(self, db_session):
        long_email = "a" * 50 + "@example.com"
        user_data = type('obj', (object,), {
            'email': long_email,
            'password': 'p'
        })
        user = cruds.create_user(db_session, user=user_data)
        assert user.email == long_email


class TestDeleteUser:
    def test_delete_user_success(self, db_session, test_user):
        result = cruds.delete_user(db_session, user_id=test_user.id)
        assert result == 1
        user = cruds.get_user(db_session, user_id=test_user.id)
        assert user is None

    def test_delete_user_not_found(self, db_session):
        result = cruds.delete_user(db_session, user_id=9999)
        assert result == 0

    def test_delete_user_negative_id(self, db_session):
        result = cruds.delete_user(db_session, user_id=-1)
        assert result == 0


class TestUpdateUser:
    def test_update_user_success(self, db_session, test_user):
        update_data = {
            'id': test_user.id,
            'email': test_user.email,
            'username': 'updatedname',
            'avatar': 'newavatar.png',
            'role': 'general',
            'is_active': True,
            'frequency_max': 1000
        }
        user_obj = type('obj', (object,), update_data)
        result = cruds.update_user(db_session, user=user_obj)
        assert result == 1
        updated_user = cruds.get_user(db_session, user_id=test_user.id)
        assert updated_user.username == "updatedname"

    def test_update_user_not_found(self, db_session):
        update_data = {
            'id': 9999,
            'email': 'test@example.com',
            'username': 'updatedname',
            'avatar': None,
            'role': 'general',
            'is_active': True,
            'frequency_max': 600
        }
        user_obj = type('obj', (object,), update_data)
        result = cruds.update_user(db_session, user=user_obj)
        assert result == 0


class TestUpdateUserPassword:
    def test_update_password_success(self, db_session, test_user):
        password_data = type('obj', (object,), {
            'id': test_user.id,
            'oldpassword': 't',
            'password': 'n'
        })
        result = cruds.update_user_password(db_session, user=password_data)
        assert result == 1
        login_result = cruds.get_user_by_login(db_session, email="test@example.com", password="n")
        assert login_result is not False

    def test_update_password_wrong_old_password(self, db_session, test_user):
        password_data = type('obj', (object,), {
            'id': test_user.id,
            'oldpassword': 'wrong',
            'password': 'n'
        })
        result = cruds.update_user_password(db_session, user=password_data)
        assert result is False

    def test_update_password_user_not_found(self, db_session):
        password_data = type('obj', (object,), {
            'id': 9999,
            'oldpassword': 'y',
            'password': 'n'
        })
        result = cruds.update_user_password(db_session, user=password_data)
        assert result is False

    def test_update_password_empty_new_password(self, db_session, test_user):
        password_data = type('obj', (object,), {
            'id': test_user.id,
            'oldpassword': 't',
            'password': ''
        })
        result = cruds.update_user_password(db_session, user=password_data)
        assert result == 1
