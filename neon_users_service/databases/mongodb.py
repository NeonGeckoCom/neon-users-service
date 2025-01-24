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

from pymongo import MongoClient
from neon_users_service.databases import UserDatabase
from neon_data_models.models.user.database import User
from neon_users_service.exceptions import UserNotFoundError


class MongoDbUserDatabase(UserDatabase):
    def __init__(self, db_host: str, db_port: int, db_user: str, db_pass: str,
                 db_name: str = "neon-users", collection_name: str = "users"):
        connection_string = f"mongodb://{db_user}:{db_pass}@{db_host}:{db_port}"
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def _db_create_user(self, user: User) -> User:
        self.collection.insert_one({**user.model_dump(),
                                    "_id": user.user_id})
        return self.read_user_by_id(user.user_id)

    def read_user_by_id(self, user_id: str) -> User:
        result = self.collection.find_one({"user_id": user_id})
        if not result:
            raise UserNotFoundError(user_id)
        return User(**result)

    def read_user_by_username(self, username: str) -> User:
        result = self.collection.find_one({"username": username})
        if not result:
            raise UserNotFoundError(username)
        return User(**result)

    def _db_update_user(self, user: User) -> User:
        update = user.model_dump()
        update.pop("user_id")
        update.pop("created_timestamp")
        self.collection.update_one({"user_id": user.user_id},
                                   {"$set": update})
        return self.read_user_by_id(user.user_id)

    def _db_delete_user(self, user: User) -> User:
        self.collection.delete_one({"user_id": user.user_id})
        return user

    def shutdown(self):
        self.client.close()
