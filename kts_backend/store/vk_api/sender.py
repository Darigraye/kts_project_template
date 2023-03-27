import asyncio
import sys
import os
import json
import sys

from aiohttp.client import ClientSession
from aiohttp import TCPConnector

from aio_pika import connect, Message
from aio_pika.abc import AbstractIncomingMessage

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from kts_backend.web.utils import build_query
from kts_backend.web.config import config_from_yaml


class Sender:
    def __init__(self):
        self.rabbit_connect = None

    async def start(self):
        self.rabbit_connect = await connect("amqp://guest:guest@localhost/")
        async with self.rabbit_connect:
            channel = await self.rabbit_connect.channel()
            await channel.set_qos(prefetch_count=1)

            queue = await channel.declare_queue(
                "task_queue_3",
                durable=True,
            )

            await queue.consume(self.send_message)

            await asyncio.Future()

    async def send_message(self, message: AbstractIncomingMessage):
        async with message.process():
            async with ClientSession(
                    connector=TCPConnector(ssl=False)
            ) as session:
                raw_data = json.loads(message.body.decode())
                config = config_from_yaml(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "..",
                        "..",
                        "etc/config.yaml",
                    )
                )
                params = {
                        "random_id": 0,
                        "peer_id": raw_data["peer_id"],
                        "group_id": config.bot.group_id,
                        "access_token": config.bot.token,
                        "message": raw_data["text"],  # TODO: учесть, что текста потом не будет (на кнопках)
                        "keyboard": raw_data["keyboard"],
                    }
                attachments = raw_data.get("photo_id")
                if attachments is not None:
                    if len(attachments) == 2:
                        params["attachment"] = ",".join(attachments)
                    else:
                        params["attachment"] = attachments

                request_link = build_query(
                    host="api.vk.com",
                    method="/method/messages.send",
                    params=params
                )

                await session.post(request_link)


def run_sender():
    sender = Sender()
    asyncio.run(sender.start())


if __name__ == "__main__":
    run_sender()
