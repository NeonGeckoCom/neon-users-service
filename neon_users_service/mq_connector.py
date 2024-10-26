from typing import Optional

import pika.channel
from ovos_config.config import Configuration
from ovos_utils import LOG

from neon_mq_connector.connector import MQConnector
from neon_mq_connector.utils.network_utils import b64_to_dict, dict_to_b64
from neon_users_service.models import MQRequest, User

from neon_users_service.service import NeonUsersService


class NeonUsersConnector(MQConnector):
    def __init__(self, config: Optional[dict], service_name: str = "neon_users_service"):
        MQConnector.__init__(self, config, service_name)
        self.vhost = '/neon_users'
        module_config = (config or Configuration()).get('neon_users_service',
                                                        {})
        self.service = NeonUsersService(module_config)

    def parse_mq_request(self, mq_req: dict) -> dict:
        mq_req = MQRequest(**mq_req)

        # Ensure supplied `user` object is consistent with request params
        if mq_req.user and mq_req.username != mq_req.user.username:
            return {"success": False,
                    "error": f"Supplied username ({mq_req.username}) "
                             f"Does not match user object "
                             f"({mq_req.user.username})"}

        if mq_req.operaion == "create":
            if not mq_req.password:
                return {"success": False,
                        "error": "Empty password provided"}
            if not mq_req.user:
                mq_req.user = User(username=mq_req.username,
                                   password_hash=mq_req.password)
            mq_req.user.password_hash = mq_req.password
            try:
                user = self.service.create_user(mq_req.user)
            except Exception as e:
                return {"success": False, "error": repr(e)}
        elif mq_req.operation == "read":
            try:
                if mq_req.password:
                    user = self.service.read_authenticated_user(mq_req.username,
                                                                mq_req.password)
                else:
                    user = self.service.read_unauthenticated_user(
                        mq_req.username)
            except Exception as e:
                return {"success": False, "error": repr(e)}
        elif mq_req.operation == "update":
            try:
                if mq_req.password:
                    mq_req.user.password_hash = mq_req.password
                user = self.service.update_user(mq_req.user)
            except Exception as e:
                return {"success": False, "error": repr(e)}
        elif mq_req.operation == "delete":
            try:
                user = self.service.delete_user(mq_req.user)
            except Exception as e:
                return {"success": False, "error": repr(e)}
        else:
            raise RuntimeError(f"Invalid operation requested: "
                               f"{mq_req.operation}")
        return {"success": True, "user": user.model_dump()}

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
            data = dict_to_b64(response)

            # queue declare is idempotent, just making sure queue exists
            channel.queue_declare(queue='neon_users_output')

            channel.basic_publish(
                exchange='',
                routing_key=request.get('routing_key',
                                        'neon_users_output'),
                body=data,
                properties=pika.BasicProperties(expiration='1000')
            )
            channel.basic_ack(method.delivery_tag)
        except Exception as e:
            LOG.exception(f"message_id={message_id}: {e}")

    def pre_run(self, **kwargs):
        self.register_consumer("neon_users_consumer", self.vhost,
                               "neon_users_input", self.handle_request,
                               auto_ack=False)
