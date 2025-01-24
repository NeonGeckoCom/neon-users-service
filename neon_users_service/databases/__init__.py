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

from abc import ABC, abstractmethod

from neon_users_service.exceptions import UserNotFoundError, UserExistsError
from neon_data_models.models.user import User


class UserDatabase(ABC):
    def create_user(self, user: User) -> User:
        """
        Add a new user to the database. Raises a `UserExistsError` if the input
        `user` already exists in the database (by `username` or `user_id`).
        @param user: `User` object to insert to the database
        @return: `User` object inserted into the database
        """
        if self._check_user_exists(user):
            raise UserExistsError(user)
        return self._db_create_user(user)

    @abstractmethod
    def _db_create_user(self, user: User) -> User:
        """
        Add a new user to the database. The `user` object has already been
        validated as unique, so this just needs to perform the database
        transaction.
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

    def update_user(self, user: User) -> User:
        """
        Update a user entry in the database. Raises a `UserNotFoundError` if
        the input user's `user_id` is not found in the database.
        @param user: `User` object to update in the database
        @return: Updated `User` object read from the database
        """
        # Lookup user to ensure they exist in the database
        existing_id = self.read_user_by_id(user.user_id)
        try:
            if self.read_user_by_username(user.username) != existing_id:
                raise UserExistsError(f"Another user with username "
                                      f"'{user.username}' already exists")
        except UserNotFoundError:
            pass
        return self._db_update_user(user)

    @abstractmethod
    def _db_update_user(self, user: User) -> User:
        """
        Update a user entry in the database. The `user` object has already been
        validated as existing and changes valid, so this just needs to perform
        the database transaction.
        @param user: `User` object to update in the database
        @return: Updated `User` object read from the database
        """

    def delete_user(self, user_id: str) -> User:
        """
        Remove a user from the database if it exists. Raises a
        `UserNotFoundError` if the input user's `user_id` is not found in the
        database.
        @param user_id: `user_id` to remove
        @return: User object removed from the database
        """
        # Lookup user to ensure they exist in the database
        user_to_delete = self.read_user_by_id(user_id)
        return self._db_delete_user(user_to_delete)

    @abstractmethod
    def _db_delete_user(self, user: User) -> User:
        """
        Remove a user from the database if it exists. The `user` object has
        already been validated as existing, so this just needs to perform the
        database transaction.
        @param user: User object to remove
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
