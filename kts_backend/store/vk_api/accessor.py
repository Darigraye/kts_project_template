import json
import os
import sys
import asyncio
from typing import TYPE_CHECKING, Optional

from aiohttp.client import ClientSession
from aiohttp import TCPConnector
from aio_pika import connect, Message as PikaMes, Message
from aio_pika.abc import AbstractIncomingMessage, DeliveryMode

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from kts_backend.web.config import config_from_yaml
from kts_backend.users.user_dataclasses import User
from kts_backend.web.utils import build_query

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class VkApiAccessor:
    def __init__(self, config):
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.ts: Optional[int] = None
        self.rabbit_session = None
        self.config = config
        self.is_running: bool = False

    async def connect(self):
        async with ClientSession(connector=TCPConnector(ssl=False)) as session:
            request_link = build_query(
                host="api.vk.com",
                method="/method/groups.getLongPollServer",
                params={
                    "group_id": self.config.bot.group_id,
                    "access_token": self.config.bot.token,
                },
            )
            async with session.get(request_link) as long_poll_response:
                response = (await long_poll_response.json())["response"]
                self.server = response["server"]
                self.key = response["key"]
                self.ts = response["ts"]
                self.session = session
                if self.rabbit_session is None:
                    self.rabbit_session = await connect(
                        "amqp://guest:guest@localhost/"
                    )
                self.is_running = True

                async with self.rabbit_session:
                    while self.is_running:
                        await self.poll()

    async def disconnect(self):
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

    async def start_consuming(self):
        if self.rabbit_session is None:
            self.rabbit_session = await connect(
                "amqp://guest:guest@localhost/"
            )

        channel = await self.rabbit_session.channel()
        exchange = channel.default_exchange

        queue = await channel.declare_queue("rpc_queue")

        async with queue.iterator() as qiterator:
            message: AbstractIncomingMessage
            async for message in qiterator:
                try:
                    async with message.process(requeue=False):
                        assert message.reply_to is not None

                        user_id = int(message.body.decode())
                        response = await self.get_user_information(user_id)
                        await exchange.publish(
                            Message(
                                body=json.dumps(response).encode(),
                                correlation_id=message.correlation_id,
                            ),
                            routing_key=message.reply_to,
                        )
                except Exception as e:
                    print(str(e))

    async def get_user_information(self, user_id: int) -> tuple[str, int]:
        request_link = build_query(
                    host="api.vk.com",
                    method="/method/users.get",
                    params={
                        "access_token": self.config.bot.token,
                        "user_ids": user_id,
                        "fields": "photo_id"
                    }
        )
        async with self.session.get(request_link) as poll_response:
            response = await poll_response.json()

        return response["response"][0].get("photo_id"), \
               response["response"][0].get("first_name"), \
               response["response"][0].get("last_name")


async def connect_and_start_consuming():
    vk_api = VkApiAccessor(config_from_yaml(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "etc/config.yaml",
        )
    ))
    await asyncio.gather(
        vk_api.connect(),
        vk_api.start_consuming()
    )


def run_vk_api():
    asyncio.run(connect_and_start_consuming())


if __name__ == "__main__":
    run_vk_api()
