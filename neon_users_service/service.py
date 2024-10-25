from typing import Optional
from ovos_config import Configuration
from neon_users_service.databases import UserDatabase


class NeonUsersService:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or Configuration().get("neon_users_service", {})
        self.database = self.init_database()

    def init_database(self) -> UserDatabase:
        module = self.config.get("module")
        module_config = self.config.get(module)
        if module == "sqlite":
            from neon_users_service.databases.sqlite import SQLiteUserDatabase
            return SQLiteUserDatabase(**module_config)
        # Other supported databases may be added here

