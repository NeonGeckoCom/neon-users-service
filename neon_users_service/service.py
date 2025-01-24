# Copyright (C) 2025 Neongecko.com Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import hashlib
import re

from copy import copy
from typing import Optional
from ovos_config import Configuration

from neon_data_models.models.api.jwt import HanaToken
from neon_users_service.databases import UserDatabase
from neon_users_service.exceptions import (ConfigurationError,
                                           AuthenticationError,
                                           UserNotMatchedError)
from neon_data_models.models.user import User


class NeonUsersService:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or Configuration().get("neon_users_service", {})
        self.database = self.init_database()
        if not self.database:
            raise ConfigurationError(f"`{self.config.get('module')}` is not a "
                                     f"valid database module.")

    def init_database(self) -> UserDatabase:
        module = self.config.get("module")
        module_config = self.config.get(module)
        if module == "sqlite":
            from neon_users_service.databases.sqlite import SQLiteUserDatabase
            return SQLiteUserDatabase(**module_config)
        elif module == "mongodb":
            from neon_users_service.databases.mongodb import MongoDbUserDatabase
            return MongoDbUserDatabase(**module_config)
        # Other supported databases may be added here

    @staticmethod
    def _ensure_hashed(password: str) -> str:
        """
        Generate the sha-256 hash for an input password to be stored in the
        database. If the password is already a valid hash string, it will be
        returned with no changes.
        @param password: Input password string to be hashed
        @retruns: A hexadecimal string representation of the sha-256 hash
        """
        if re.compile(r"^[a-f0-9]{64}$").match(password):
            password_hash = password
        else:
            password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return password_hash

    def create_user(self, user: User) -> User:
        """
        Helper to create a new user. Includes a check that the input password
        hash is valid, replacing string passwords with hashes as necessary.
        @param user: The user to be created
        @returns: The user as added to the database
        """
        # Create a copy to prevent modifying the input object
        user = copy(user)
        user.password_hash = self._ensure_hashed(user.password_hash)
        return self.database.create_user(user)

    def _read_user(self, user_spec: str, password: Optional[str] = None,
                   auth_token: Optional[HanaToken] = None) -> User:
        user = self.database.read_user(user_spec)
        if password and self._ensure_hashed(password) == user.password_hash:
            return user
        elif auth_token and any((tok.jti == f"{auth_token.jti}.refresh"
                                 for tok in user.tokens)):
            return user
        else:
            user.password_hash = None
            user.tokens = []
            return user

    def read_unauthenticated_user(self, user_spec: str) -> User:
        """
        Helper to get a user from the database with sensitive data removed.
        This is what most lookups should return; `authenticate_user` can be
        used to get an un-redacted User object.
        @param user_spec: username or user_id to retrieve
        @returns: Redacted User object with sensitive information removed
        """
        return self._read_user(user_spec)

    def read_authenticated_user(self, username: str,
                                password: Optional[str] = None,
                                auth_token: Optional[HanaToken] = None) -> User:
        """
        Helper to get a user from the database, only if the requested username
        and password match a database entry.
        @param username: The username or user ID to retrieve
        @param password: The hashed or plaintext password for the username
        @param auth_token: A valid authentication token for the username
        @returns: User object from the database if authentication was successful
        """
        # This will raise a `UserNotFound` exception if the user doesn't exist
        if password:
            user = self._read_user(username, password)
        elif auth_token:
            user = self._read_user(username, auth_token=auth_token)
        else:
            raise AuthenticationError("No password or token provided")
        if user.password_hash is None:
            raise AuthenticationError(f"Invalid password for {username}")
        return user

    def update_user(self, user: User) -> User:
        """
        Helper to update a user. If the supplied user's password is not defined,
        an `AuthenticationError` will be raised.
        @param user: The updated user object to update in the database
        @retruns: User object as it exists in the database, after updating
        """
        # Create a copy to prevent modifying the input object
        user = copy(user)
        if not user.password_hash:
            raise ValueError("Supplied user password is empty")
        if not isinstance(user.tokens, list):
            raise ValueError("Supplied tokens configuration is not a list")
        user.password_hash = self._ensure_hashed(user.password_hash)
        # This will raise a `UserNotFound` exception if the user doesn't exist
        return self.database.update_user(user)

    def delete_user(self, user: User) -> User:
        """
        Helper to remove a user from the database. If the supplied user does not
        match any database entry, a `UserNotFoundError` will be raised.
        @param user: The user object to remove from the database
        @returns: User object removed from the database
        """
        db_user = self.database.read_user_by_id(user.user_id)
        if db_user != user:
            raise UserNotMatchedError(user)
        return self.database.delete_user(user.user_id)

    def shutdown(self):
        """
        Shutdown the service.
        """
        self.database.shutdown()
