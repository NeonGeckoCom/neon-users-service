import hashlib
import os
from unittest import TestCase
from os.path import join, dirname, isfile

from neon_users_service.databases import UserDatabase
from neon_users_service.databases.sqlite import SQLiteUserDatabase
from neon_users_service.exceptions import ConfigurationError, AuthenticationError, UserNotFoundError
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

    def test_authenticate_user(self):
        service = NeonUsersService(self.test_config)
        string_password = "super secret password"
        hashed_password = hashlib.sha256(string_password.encode()).hexdigest()
        user_1 = service.create_user(User(username="user",
                                          password_hash=hashed_password))
        auth_1 = service.authenticate_user("user", string_password)
        self.assertEqual(auth_1, user_1)
        auth_2 = service.authenticate_user("user", hashed_password)
        self.assertEqual(auth_2, user_1)

        with self.assertRaises(AuthenticationError):
            service.authenticate_user("user", "bad password")

        with self.assertRaises(UserNotFoundError):
            service.authenticate_user("user_1", hashed_password)

