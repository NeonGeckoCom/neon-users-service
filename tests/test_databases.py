import json

from os import remove, environ
from os.path import join, dirname, isfile
from time import time
from typing import Optional
from unittest import TestCase
from uuid import uuid4

from neon_users_service.databases.sqlite import SQLiteUserDatabase
from neon_users_service.exceptions import UserExistsError, UserNotFoundError
from neon_data_models.models.user import User
from neon_data_models.enum import AccessRoles


class TestSqlite(TestCase):
    test_db_file = join(dirname(__file__), 'test_db.sqlite')
    database: Optional[SQLiteUserDatabase] = None

    def setUp(self):
        if isfile(self.test_db_file):
            remove(self.test_db_file)
        self.database = SQLiteUserDatabase(self.test_db_file)

    def tearDown(self):
        self.database.shutdown()

    def test_create_user(self):
        # Create a unique user
        create_time = round(time())
        user = self.database.create_user(User(username="test_user",
                                              password_hash="test123"))
        self.assertEqual(user.username, "test_user")
        self.assertEqual(user.password_hash, "test123")
        self.assertIsInstance(user.user_id, str)
        self.assertAlmostEqual(user.created_timestamp, create_time, delta=2)

        # Fail on an existing username
        with self.assertRaises(UserExistsError):
            self.database.create_user(User(username=user.username,
                                           password_hash="test"))
        # Fail on an existing user ID
        with self.assertRaises(UserExistsError):
            self.database.create_user(User(username="new_user",
                                           password_hash="test",
                                           user_id=user.user_id))

        # Second user
        create_time = round(time())
        user2 = self.database.create_user(User(username="test_user_1",
                                               password_hash="test"))
        self.assertNotEqual(user, user2)
        self.assertAlmostEqual(user2.created_timestamp, create_time, delta=2)

    def test_read_user(self):
        user = self.database.create_user(User(username="test",
                                              password_hash="test123"))
        # Retrieve valid user by user_id and username
        self.assertEqual(self.database.read_user_by_id(user.user_id), user)
        self.assertEqual(self.database.read_user_by_username(user.username),
                         user)

        # Retrieve using `read_user` method from base class
        self.assertEqual(self.database.read_user(user.user_id), user)
        self.assertEqual(self.database.read_user(user.username), user)

        # Retrieve nonexistent user raises exceptions
        with self.assertRaises(UserNotFoundError):
            self.database.read_user_by_id("fake-user-id")
        with self.assertRaises(UserNotFoundError):
            self.database.read_user_by_username("fake-user-username")

    def test_update_user(self):
        create_time = round(time())
        user = self.database.create_user(User(username="test_user",
                                              password_hash="test123"))
        self.assertEqual(user.username, "test_user")
        self.assertAlmostEqual(user.created_timestamp, create_time, delta=2)

        # Test Change Username and Setting
        user.username = "updated_name"
        user.permissions.node = AccessRoles.ADMIN
        user.created_timestamp = round(time())

        # Test update
        user2 = self.database.update_user(user)
        self.assertEqual(user2.username, "updated_name")
        self.assertEqual(user2.permissions.node, AccessRoles.ADMIN)
        # `created_timestamp` is immutable
        self.assertEqual(user2.created_timestamp, user.created_timestamp)
        self.assertAlmostEqual(user2.created_timestamp, create_time, delta=2)
        # old username is no longer in the database
        with self.assertRaises(UserNotFoundError):
            self.database.read_user_by_username("test_user")
        # new username does resolve
        self.assertEqual(self.database.read_user_by_username("updated_name"),
                         user2)
        self.assertEqual(self.database.read_user_by_id(user2.user_id), user2)

    def test_delete_user(self):
        with self.assertRaises(UserNotFoundError):
            self.database.delete_user("user-id")
        user = self.database.create_user(User(username="test_delete",
                                              password_hash="password"))
        # Removal requires UID, not just username
        with self.assertRaises(UserNotFoundError):
            self.database.delete_user(user.username)

        removed_user = self.database.delete_user(user.user_id)
        self.assertEqual(user, removed_user)

        with self.assertRaises(UserNotFoundError):
            self.database.read_user_by_id(user.user_id)
        with self.assertRaises(UserNotFoundError):
            self.database.read_user_by_username(user.username)


class TestMongoDb(TestCase):
    test_config = json.loads(environ.get("MONGO_TEST_CONFIG"))
    test_config['collection_name'] = f"{test_config['collection_name']}{time()}"
    from neon_users_service.databases.mongodb import MongoDbUserDatabase
    database = MongoDbUserDatabase(**test_config)
    test_user = User(username="test_user", password_hash="password")

    def tearDown(self):
        try:
            self.database.delete_user(self.test_user.user_id)
        except UserNotFoundError:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.database.db.drop_collection(cls.test_config['collection_name'])
        cls.database.shutdown()

    def test_create_user(self):
        # Create User
        user = self.database.create_user(self.test_user)
        self.assertEqual(user, self.test_user)

        # Existing user fails
        with self.assertRaises(UserExistsError):
            self.database.create_user(self.test_user)

    def test_read_user(self):
        user = self.database.create_user(self.test_user)

        by_id = self.database.read_user_by_id(user.user_id)
        by_name = self.database.read_user_by_username(user.username)
        self.assertEqual(by_id, user)
        self.assertEqual(by_name, user)

        # Invalid inputs
        with self.assertRaises(UserNotFoundError):
            self.database.read_user_by_id(user.username)
        with self.assertRaises(UserNotFoundError):
            self.database.read_user_by_username(user.user_id)

    def test_update_user(self):
        user = self.database.create_user(self.test_user)

        user.password_hash = "new_password"
        user.permissions.node = AccessRoles.OWNER

        # Invalid change request
        fake_time = round(time()) + 10
        user.created_timestamp = fake_time

        updated = self.database.update_user(user)
        self.assertNotEqual(user.created_timestamp,
                            updated.created_timestamp, f"fake={fake_time}")
        self.assertEqual(self.test_user.created_timestamp,
                         updated.created_timestamp)

        self.assertEqual(updated.password_hash, user.password_hash)
        self.assertEqual(updated.permissions.node, AccessRoles.OWNER)

        # Invalid update request (user not exists
        user.user_id = str(uuid4())
        with self.assertRaises(UserNotFoundError):
            self.database.update_user(user)

    def test_delete_user(self):
        user = self.database.create_user(self.test_user)

        # Delete valid user
        self.assertEqual(user, self.database.delete_user(user.user_id))

        with self.assertRaises(UserNotFoundError):
            self.database.delete_user(user.user_id)
