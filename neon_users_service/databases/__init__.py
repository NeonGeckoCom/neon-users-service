from abc import ABC, abstractmethod

from neon_users_service.exceptions import UserNotFoundError
from neon_data_models.models.user.database import User


class UserDatabase(ABC):
    @abstractmethod
    def create_user(self, user: User) -> User:
        """
        Add a new user to the database. Raises a `UserExistsError` if the input
        `user` already exists in the database (by `username` or `user_id`).
        @param user: `User` object to insert to the database
        @return: `User` object inserted into the database
        """

    @abstractmethod
    def read_user_by_id(self, user_id: str) -> User:
        """
        Get a `User` object by `user_id`. Raises a `UserNotFoundError` if the
        input `user_id` is not found in the database
        @param user_id: `user_id` to look up
        @return: `User` object parsed from the database
        """

    @abstractmethod
    def read_user_by_username(self, username: str) -> User:
        """
        Get a `User` object by `username`. Note that `username` is not
        guaranteed to be static. Raises a `UserNotFoundError` if the
        input `username` is not found in the database
        @param username: `username` to look up
        @return: `User` object parsed from the database
        """

    def read_user(self, user_spec: str) -> User:
        """
        Get a `User` object by username or user_id. Raises a 
        `UserNotFoundError` if the user is not found. `user_id` is given priority
        over `username`; it is possible (though unlikely) that a username
        exists with the same spec as another user's user_id.
        """
        try:
            return self.read_user_by_id(user_spec)
        except UserNotFoundError:
            return self.read_user_by_username(user_spec)

    @abstractmethod
    def update_user(self, user: User) -> User:
        """
        Update a user entry in the database. Raises a `UserNotFoundError` if
        the input user's `user_id` is not found in the database.
        """

    @abstractmethod
    def delete_user(self, user_id: str) -> User:
        """
        Remove a user from the database if it exists. Raises a
        `UserNotFoundError` if the input user's `user_id` is not found in the
        database.
        @param user_id: `user_id` to remove
        @return: User object removed from the database
        """

    def _check_user_exists(self, user: User) -> bool:
        """
        Check if a user already exists with the given `username` or `user_id`.
        """
        try:
            # If username is defined, raise an exception
            if self.read_user_by_username(user.username):
                return True
        except UserNotFoundError:
            pass
        try:
            # If user ID is defined, it was likely passed to the `User` object
            # instead of allowing the Factory to generate a new one.
            if self.read_user_by_id(user.user_id):
                return True
        except UserNotFoundError:
            pass
        return False

    def shutdown(self):
        """
        Perform any cleanup when a database is no longer being used
        """
        pass
