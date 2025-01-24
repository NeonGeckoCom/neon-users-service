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

class UserExistsError(Exception):
    """
    Raised when trying to create a user with a username that already exists.
    """


class UserNotFoundError(Exception):
    """
    Raised when trying to look up a user that does not exist.
    """


class UserNotMatchedError(Exception):
    """
    Raised when two `User` objects are expected to match and do not.
    """


class ConfigurationError(KeyError):
    """
    Raised when service configuration is not valid.
    """


class AuthenticationError(ValueError):
    """
    Raised when authentication fails for an existing valid user.
    """


class PermissionsError(Exception):
    """
    Raised when a user does not have sufficient permissions to perform the
    requested action.
    """


class DatabaseError(RuntimeError):
    """
    Raised when a database-related error occurs.
    """