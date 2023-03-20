import os
import sys

from asyncio import Task, create_task, run, Future
from typing import TYPE_CHECKING, Optional

from aio_pika.abc import AbstractIncomingMessage

from aio_pika import connect, Message

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from kts_backend.web.app import app
from kts_backend.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store: Store = store
        self.is_running: bool = False
        self.poll_task: Optional[Task] = None
        self.rabbit_connect = None
        self.rabbit_channel = None

    async def start(self):
    #    self.poll_task = create_task(self.poll())
        self.is_running = True
        self.rabbit_connect = await connect('amqp://guest:guest@localhost/')
        await self.poll()

    async def stop(self):
        self.is_running = False
        self.poll_task = None

    async def poll(self):
        async with self.rabbit_connect:
            self.rabbit_channel = await self.rabbit_connect.channel()
            await self.rabbit_channel.set_qos(prefetch_count=1)

            queue = await self.rabbit_channel.declare_queue(
                "task_queue_1",
                durable=True,
            )

            await queue.consume(self.callback)
            await Future()

    async def callback(self, message: AbstractIncomingMessage):
        async with message.process():
            queue = await self.rabbit_channel.declare_queue(
                "task_queue_2",
                durable=True,
            )
            await self.rabbit_channel.default_exchange.publish(message, routing_key='task_queue_2')

        # while self.is_running:
        #     updates = await self.store.vk_api.poll()
        #     await self.bot_manager.handle_updates(updates)


if __name__ == '__main__':
    poller = Poller(app.store)
    run(poller.start())
