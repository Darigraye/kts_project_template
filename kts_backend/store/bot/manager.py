import asyncio
import json
import os
import sys

from asyncio import Future
from typing import TYPE_CHECKING

from aio_pika import connect, Message
from aio_pika.abc import AbstractIncomingMessage, DeliveryMode

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


from kts_backend.web.app import Application, app


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.rabbit_connect = None
        self.rabbit_channel = None

    async def start(self):
        self.rabbit_connect = await connect('amqp://guest:guest@localhost/')
        async with self.rabbit_connect:
            self.rabbit_channel = await self.rabbit_connect.channel()
            await self.rabbit_channel.set_qos(prefetch_count=1)

            queue = await self.rabbit_channel.declare_queue(
                "task_queue_2",
                durable=True,
            )

            await queue.consume(self.handle_updates)
            await Future()

    async def handle_updates(self, message: AbstractIncomingMessage):
        async with message.process():
            raw_data = json.loads(message.body.decode())
            for update in raw_data:
                if update['type'] == 'message_new':
                    queue = await self.rabbit_channel.declare_queue(
                        "task_queue_3",
                        durable=True,
                    )
                    new_message_body = {
                                        'user_id': update['object']['message']['from_id'],
                                        'text': update['object']['message']['text'],
                                        'peer_id': update['object']['message']['peer_id']
                                        }

                    await self.rabbit_channel.default_exchange.publish(Message(json.dumps(new_message_body).encode(),
                                                                               delivery_mode=DeliveryMode.PERSISTENT),
                                                                       routing_key='task_queue_3')


if __name__ == '__main__':
    bot = BotManager(app)
    asyncio.run(bot.start())
