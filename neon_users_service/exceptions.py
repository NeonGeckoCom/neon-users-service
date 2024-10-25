
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


class DatabaseError(RuntimeError):
    """
    Raised when a database-related error occurs.
    """