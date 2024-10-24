
class UserExistsError(Exception):
    """
    Raised when trying to create a user with a username that already exists.
    """


class UserNotExistsError(Exception):
    """
    Raised when trying to look up a user that does not exist.
    """