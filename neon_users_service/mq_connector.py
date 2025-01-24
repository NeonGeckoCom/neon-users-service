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

from typing import Optional

import pika.channel
from ovos_utils import LOG
from ovos_config.config import Configuration

from neon_data_models.enum import AccessRoles
from neon_mq_connector.connector import MQConnector
from neon_mq_connector.utils.network_utils import b64_to_dict, dict_to_b64
from neon_users_service.exceptions import UserNotFoundError, AuthenticationError, UserNotMatchedError, UserExistsError
from neon_data_models.models.api.mq import (UserDbRequest, CreateUserRequest,
                                            ReadUserRequest, UpdateUserRequest,
                                            DeleteUserRequest)

from neon_users_service.service import NeonUsersService


class NeonUsersConnector(MQConnector):
    def __init__(self, config: Optional[dict],
                 service_name: str = "neon_users_service"):
        MQConnector.__init__(self, config, service_name)
        self.vhost = '/neon_users'
        module_config = (config or Configuration()).get('neon_users_service',
                                                        {})
        self.service = NeonUsersService(module_config)

    def parse_mq_request(self, mq_req: dict) -> dict:
        """
        Handle a request to interact with the user database.

        Create: Accepts a new User object and adds it to the database
        Read: Accepts a Username or User ID and either an Access Token or
            Password. If the authenticating user is not the same as the requested
            user, then sensitive authentication information will be redacted from
            the returned object.
        Update: Updates the database with the supplied User. If
            `auth_username` and `auth_password` are supplied, they will be used
            to determine permissions for this transaction, otherwise permissions
            will be read for the user being updated. A user may modify their own
            configuration (except permissions) and any user with a diana role of
            `ADMIN` or higher may modify other users.
        Delete: Deletes a User from the database. The request object must match
            the database entry exactly, so no additional validation is required.
        """
        mq_req = UserDbRequest(**mq_req)

        try:
            if isinstance(mq_req, CreateUserRequest):
                user = self.service.create_user(mq_req.user)
            elif isinstance(mq_req, ReadUserRequest):
                if mq_req.user_spec == mq_req.auth_user_spec:
                    user = self.service.read_authenticated_user(mq_req.user_spec,
                                                                mq_req.password,
                                                                mq_req.access_token)
                else:
                    auth_user = self.service.read_authenticated_user(
                        mq_req.auth_user_spec, mq_req.password,
                        mq_req.access_token)
                    if auth_user.permissions.users < AccessRoles.USER:
                        raise PermissionError(f"User {auth_user.username} does "
                                              f"not have permission to read "
                                              f"other users")
                    user = self.service.read_unauthenticated_user(
                        mq_req.user_spec)
            elif isinstance(mq_req, UpdateUserRequest):
                # Get the authenticating user, maybe raising an AuthenticationError
                auth = self.service.read_authenticated_user(mq_req.auth_username,
                                                            mq_req.auth_password)
                if auth.permissions.users < AccessRoles.ADMIN:
                    if auth.user_id != mq_req.user.user_id:
                        raise PermissionError(f"User {auth.username} does not "
                                              f"have permission to modify "
                                              f"other users")
                    # Do not allow this non-admin to change their permissions
                    mq_req.user.permissions = auth.permissions

                user = self.service.update_user(mq_req.user)
            elif isinstance(mq_req, DeleteUserRequest):
                # If the passed User object isn't an exact match, this will fail
                user = self.service.delete_user(mq_req.user)
            else:
                raise RuntimeError(f"Unsupported operation requested: "
                                   f"{mq_req}")
            return {"success": True, "user": user.model_dump()}
        except UserExistsError:
            return {"success": False, "error": "User already exists",
                    "code": 409}
        except UserNotFoundError:
            return {"success": False, "error": "User does not exist",
                    "code": 404}
        except UserNotMatchedError:
            return {"success": False, "error": "Invalid user", "code": 401}
        except AuthenticationError:
            return {"success": False, "error": "Invalid username or password",
                    "code": 401}
        except Exception as e:
            return {"success": False, "error": repr(e), "code": 500}

    def handle_request(self,
                       channel: pika.channel.Channel,
                       method: pika.spec.Basic.Deliver,
                       _: pika.spec.BasicProperties,
                       body: bytes):
        """
        Handles input MQ request objects.
        @param channel: MQ channel object (pika.channel.Channel)
        @param method: MQ return method (pika.spec.Basic.Deliver)
        @param _: MQ properties (pika.spec.BasicProperties)
        @param body: request body (bytes)
        """
        message_id = None
        try:
            if not isinstance(body, bytes):
                raise TypeError(f'Invalid body received, expected bytes string;'
                                f' got: {type(body)}')
            request = b64_to_dict(body)
            message_id = request.get("message_id")
            response = self.parse_mq_request(request)
            response["message_id"] = message_id
            data = dict_to_b64(response)

            routing_key = request.get('routing_key', 'neon_users_output')
            # queue declare is idempotent, just making sure queue exists
            channel.queue_declare(queue=routing_key)

            channel.basic_publish(
                exchange='',
                routing_key=routing_key,
                body=data,
                properties=pika.BasicProperties(expiration='1000')
            )
            LOG.info(f"Sent response to queue {routing_key}: {response}")
            channel.basic_ack(method.delivery_tag)
        except Exception as e:
            LOG.exception(f"message_id={message_id}: {e}")

    def pre_run(self, **kwargs):
        self.register_consumer("neon_users_consumer", self.vhost,
                               "neon_users_input", self.handle_request,
                               auto_ack=False)
