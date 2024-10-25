import hashlib
import os
from unittest import TestCase
from os.path import join, dirname, isfile

from neon_users_service.databases import UserDatabase
from neon_users_service.databases.sqlite import SQLiteUserDatabase
from neon_users_service.exceptions import ConfigurationError, AuthenticationError, UserNotFoundError, \
    UserNotMatchedError
from neon_users_service.models import User
from neon_users_service.service import NeonUsersService


class TestUsersService(TestCase):
    test_db_path = join(dirname(__file__), 'test_db.sqlite')
    test_config = {"module": "sqlite",
                   "sqlite": {"db_path": test_db_path}}

    def setUp(self):
        if isfile(self.test_db_path):
            os.remove(self.test_db_path)

    def test_create_service(self):
        # Create with default config
        service = NeonUsersService()
        self.assertIsNotNone(service.config)
        self.assertIsInstance(service.database, UserDatabase)
        service.shutdown()

        # Create with valid passed configuration
        service = NeonUsersService(self.test_config)
        self.assertIsInstance(service.database, SQLiteUserDatabase)
        self.assertTrue(isfile(self.test_db_path))
        service.shutdown()

        # Create with invalid configuration
        with self.assertRaises(ConfigurationError):
            NeonUsersService({"module": None})

    def test_create_user(self):
        service = NeonUsersService(self.test_config)
        string_password = "super secret password"
        hashed_password = hashlib.sha256(string_password.encode()).hexdigest()
        user_1 = service.create_user(User(username="user_1",
                                          password_hash=hashed_password))
        input_user_2 = User(username="user_2", password_hash=string_password)
        user_2 = service.create_user(input_user_2)
        self.assertEqual(user_1.password_hash, hashed_password)
        self.assertEqual(user_2.password_hash, hashed_password)
        # The input object should not be modified
        self.assertNotEqual(user_2, input_user_2)
        service.shutdown()

    def test_read_authenticated_user(self):
        service = NeonUsersService(self.test_config)
        string_password = "super secret password"
        hashed_password = hashlib.sha256(string_password.encode()).hexdigest()
        user_1 = service.create_user(User(username="user",
                                          password_hash=hashed_password))
        auth_1 = service.read_authenticated_user("user", string_password)
        self.assertEqual(auth_1, user_1)
        auth_2 = service.read_authenticated_user("user", hashed_password)
        self.assertEqual(auth_2, user_1)

        with self.assertRaises(AuthenticationError):
            service.read_authenticated_user("user", "bad password")

        with self.assertRaises(UserNotFoundError):
            service.read_authenticated_user("user_1", hashed_password)
        service.shutdown()

    def test_read_unauthenticated_user(self):
        service = NeonUsersService(self.test_config)
        user_1 = service.create_user(User(username="user",
                                          password_hash="test"))
        read_user = service.read_unauthenticated_user("user")
        self.assertEqual(read_user, service.read_unauthenticated_user(user_1.user_id))
        self.assertIsNone(read_user.password_hash)
        self.assertEqual(read_user.tokens, [])
        read_user.password_hash = user_1.password_hash
        read_user.tokens = user_1.tokens
        self.assertEqual(user_1, read_user)

        with self.assertRaises(UserNotFoundError):
            service.read_unauthenticated_user("not_a_user")
        service.shutdown()

    def test_update_user(self):
        service = NeonUsersService(self.test_config)
        user_1 = service.create_user(User(username="user",
                                          password_hash="test"))

        # Valid update
        user_1.username = "new_username"
        updated_user = service.update_user(user_1)
        self.assertEqual(updated_user, user_1)

        # Invalid password values
        updated_user.password_hash = None
        with self.assertRaises(ValueError):
            service.update_user(updated_user)
        updated_user.password_hash = ""
        with self.assertRaises(ValueError):
            service.update_user(updated_user)

        # Valid password values
        updated_user.password_hash = user_1.password_hash
        updated_user = service.update_user(updated_user)
        self.assertEqual(updated_user.password_hash, user_1.password_hash)

        # Input plaintext passwords should be hashed
        updated_user.password_hash = "test"
        new_updated_user = service.update_user(updated_user)
        self.assertNotEqual(updated_user.password_hash,
                            new_updated_user.password_hash)
        self.assertEqual(new_updated_user.password_hash, user_1.password_hash)

        # Invalid token values
        updated_user.tokens = None
        with self.assertRaises(ValueError):
            service.update_user(updated_user)

        service.shutdown()

    def test_delete_user(self):
        service = NeonUsersService(self.test_config)
        user_1 = service.create_user(User(username="user",
                                          password_hash="test"))
        invalid_user = User(username="user", password_hash="test")
        incomplete_user = service.read_unauthenticated_user(user_1.user_id)

        with self.assertRaises(UserNotFoundError):
            service.delete_user(invalid_user)

        with self.assertRaises(UserNotMatchedError):
            service.delete_user(incomplete_user)

        deleted = service.delete_user(user_1)
        self.assertEqual(deleted, user_1)

        with self.assertRaises(UserNotMatchedError):
            service.read_unauthenticated_user(user_1.user_id)

        service.shutdown()
