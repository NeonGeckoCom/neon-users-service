# Copyright (C) 2008-2026 Neongecko.com Inc.
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

from neon_data_models.enum import AccessRoles
from neon_data_models.models.user.database import User, PermissionsConfig

from neon_users_service.service import NeonUsersService

def create_admin_user(username: str, password: str) -> User:
    """
    Create an admin-privileged user in the database. Note that there is a
    higher "OWNER" role that is not defined here; this is intentionally
    set to `ADMIN` as the minimal requirement to perform routine tasks.
    @param username: Username of admin user to create
    @param password: Password of user to create
    @returns: Created User object
    """
    service = NeonUsersService()
    admin_permissions = PermissionsConfig(klat=AccessRoles.ADMIN,
                                          core=AccessRoles.ADMIN,
                                          diana=AccessRoles.ADMIN,
                                          users=AccessRoles.ADMIN,
                                          node=AccessRoles.ADMIN,
                                          hub=AccessRoles.ADMIN,
                                          llm=AccessRoles.ADMIN)

    # `password` is not hashed, but the service automatically handles hashing
    new_user = User(username=username, password_hash=password,
                    permissions=admin_permissions)

    created_user = service.create_user(new_user)
    return created_user
