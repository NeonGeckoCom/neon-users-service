from pymongo import MongoClient
from neon_users_service.databases import UserDatabase
from neon_data_models.models.user.database import User
from neon_users_service.exceptions import UserNotFoundError


class MongoDbUserDatabase(UserDatabase):
    def __init__(self, db_host: str, db_port: int, db_user: str, db_pass: str,
                 db_name: str = "neon-users", collection_name: str = "users"):
        connection_string = f"mongodb://{db_user}:{db_pass}@{db_host}:{db_port}"
        self.client = MongoClient(connection_string)
        db = self.client[db_name]
        self.collection = db[collection_name]

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
