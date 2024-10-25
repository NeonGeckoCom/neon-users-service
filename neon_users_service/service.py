import hashlib
import re
from copy import copy
from typing import Optional
from ovos_config import Configuration
from neon_users_service.databases import UserDatabase
from neon_users_service.exceptions import ConfigurationError, AuthenticationError
from neon_users_service.models import User


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

    def authenticate_user(self, username: str, password: str) -> User:
        """
        Helper to get a user from the database, only if the requested username
        and password match a database entry.
        @param username: The username or user ID to retrieve
        @param password: The hashed or plaintext password for the username
        @returns: User object from the database if authentication was successful
        """
        # This will raise a `UserNotFound` exception if the user doesn't exist
        user = self.database.read_user(username)

        hashed_password = self._ensure_hashed(password)
        if hashed_password != user.password_hash:
            raise AuthenticationError(f"Invalid password for {username}")
        return user

    def shutdown(self):
        """
        Shutdown the service.
        """
        self.database.shutdown()
