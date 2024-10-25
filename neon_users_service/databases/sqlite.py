import json

from os import makedirs
from os.path import expanduser, dirname
from sqlite3 import connect, Cursor
from typing import Optional

from neon_users_service.databases import UserDatabase
from neon_users_service.exceptions import UserNotFoundError, UserExistsError
from neon_users_service.models import User, AccessRoles


class SQLiteUserDatabase(UserDatabase):
    def __init__(self, db_path: Optional[str] = None):
        db_path = expanduser(db_path or "~/.local/share/neon/user-db.sqlite")
        makedirs(dirname(db_path), exist_ok=True)
        self.connection = connect(db_path)
        self.connection.execute(
            '''CREATE TABLE IF NOT EXISTS users
            (user_id text,
             created_timestamp integer,
             username text,
             user_object text)'''
        )
        self.connection.commit()

    def create_user(self, user: User) -> User:
        if self._check_user_exists(user):
            raise UserExistsError(user)

        self.connection.execute(
            f'''INSERT INTO users VALUES 
            ('{user.user_id}',
            '{user.created_timestamp}',
            '{user.username}',
            '{user.model_dump_json()}')'''
        )
        self.connection.commit()
        return user

    @staticmethod
    def _parse_lookup_results(user_spec: str, cursor: Cursor):
        rows = cursor.fetchall()
        cursor.close()

        if len(rows) > 1:
            # TODO: Custom exception
            raise RuntimeError(f"User with spec '{user_spec}' has duplicate entries!")
        elif len(rows) == 0:
            raise UserNotFoundError(user_spec)
        return rows[0][0]

    def read_user_by_id(self, user_id: str) -> User:
        cursor = self.connection.cursor()
        cursor.execute(
            f'''SELECT user_object FROM users WHERE
            user_id = '{user_id}'
            '''
        )
        return User(**json.loads(self._parse_lookup_results(user_id, cursor)))

    def read_user_by_username(self, username: str) -> User:
        cursor = self.connection.cursor()
        cursor.execute(
            f'''SELECT user_object FROM users WHERE
            username = '{username}'
            '''
        )
        return User(**json.loads(self._parse_lookup_results(username, cursor)))

    def update_user(self, user: User) -> User:
        # Lookup user to ensure they exist in the database
        existing_id = self.read_user_by_id(user.user_id)
        try:
            if self.read_user_by_username(user.username) != existing_id:
                raise UserExistsError(f"Another user with username "
                                      f"'{user.username}' already exists")
        except UserNotFoundError:
            pass
        self.connection.execute(
            f'''UPDATE users SET username = '{user.username}',
            user_object = '{user.model_dump_json()}' 
            WHERE user_id = '{user.user_id}'
            '''
        )
        self.connection.commit()
        return self.read_user_by_id(user.user_id)

    def delete_user(self, user_id: str) -> User:
        # Lookup user to ensure they exist in the database
        user_to_delete = self.read_user_by_id(user_id)
        self.connection.execute(f"DELETE FROM users WHERE user_id = '{user_id}'")
        self.connection.commit()
        return user_to_delete

    def shutdown(self):
        self.connection.close()
