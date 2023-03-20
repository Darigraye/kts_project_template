import json
from typing import TYPE_CHECKING, Optional

from aiohttp.client import ClientSession
from aiohttp import TCPConnector
from aio_pika import connect, Message as PikaMes
from aio_pika.abc import AbstractIncomingMessage, DeliveryMode

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.users.user_dataclasses import User
from ...web.utils import build_query

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.ts: Optional[int] = None
        self.rabbit_session = None
        self.app = app
        self.is_running: bool = False

    async def connect(self, app: "Application"):
        async with ClientSession(connector=TCPConnector(ssl=False)) as session:
            request_link = build_query(
                host="api.vk.com",
                method="/method/groups.getLongPollServer",
                params={
                    "group_id": self.app.config.bot.group_id,
                    "access_token": self.app.config.bot.token,
                },
            )
            async with session.get(request_link) as long_poll_response:
                response = (await long_poll_response.json())["response"]
                self.server = response["server"]
                self.key = response["key"]
                self.ts = response["ts"]
                self.session = session
                self.rabbit_session = await connect(
                    "amqp://guest:guest@localhost/"
                )
                self.is_running = True

                async with self.rabbit_session:
                    while self.is_running:
                        await self.poll()

    async def disconnect(self, app: "Application"):
        await self.session.close()

    async def poll(self):
        request_link = (
            f"{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait=25"
        )
        async with self.session.get(request_link) as poll_response:
            response = await poll_response.json()
            self.ts = response["ts"]

        channel = await self.rabbit_session.channel()

        queue = await channel.declare_queue(
            "task_queue_1",
            durable=True,
        )

        message_body = json.dumps(response["updates"])
        await channel.default_exchange.publish(
            PikaMes(
                message_body.encode(), delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key="task_queue_1",
        )

    async def get_chat_information(self, chat_id: int) -> list[User]:
        request_link = build_query(
            host="api.vk.com",
            method="/method/messages.getConversationMembers",
            params={
                "access_token": self.app.config.bot.token,
                "peer_id": chat_id + 2000000000,
            },
        )
        async with self.session.get(request_link) as poll_response:
            response = await poll_response.json()

        users = [
            User(
                profile_id=user["id"],
                name=user["first_name"],
                last_name=user["last_name"],
            )
            for user in response["profiles"]
        ]

        return users
