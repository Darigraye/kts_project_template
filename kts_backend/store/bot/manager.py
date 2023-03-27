import asyncio
import json
import os
import sys

from math import log
from asyncio import Future
from typing import TYPE_CHECKING, Optional

from aio_pika import connect, Message
from aio_pika.abc import AbstractIncomingMessage, DeliveryMode
from aiohttp import ClientSession, TCPConnector

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from kts_backend.web.config import config_from_yaml
from kts_backend.web.utils import build_query
from kts_backend.games.game_tree import GameTree
from kts_backend.web.app import application, Application


class BotManager:
    state_machine: dict[int, dict[str, Optional[str | dict[int, str] | GameTree]]] = {}
    app: Application = application

    def __init__(self):
        self.rabbit_connect = None
        self.rabbit_channel = None

    async def start(self):
        self.rabbit_connect = await connect("amqp://guest:guest@localhost/")
        async with self.rabbit_connect:
            self.rabbit_channel = await self.rabbit_connect.channel()
            await self.rabbit_channel.set_qos(prefetch_count=1)

            queue = await self.rabbit_channel.declare_queue(
                "task_queue_2",
                durable=True,
            )

            await queue.consume(self.handle_updates)
            await Future()

    @staticmethod
    def build_button(label, color, payload="", type_button="callback"):
        return {
            "action": {
                "type": type_button,
                "payload": payload,
                "label": label
            },
            "color": color
        }

    @classmethod
    async def registration_user(cls, update):
        chat_id = update["object"]["peer_id"]
        user_id = update["object"]["user_id"]

        photo_id = await cls.app.store.game.get_photo_id(user_id)

        if user_id not in cls.state_machine[chat_id]["id_participants"] and photo_id is not None:
            cls.state_machine[chat_id]["id_participants"][user_id] = photo_id

    @classmethod
    async def ready_to_start(cls, update) -> bool:
        chat_id = update["object"]["peer_id"]
        number_participants = len(cls.state_machine[chat_id]["id_participants"])

        return number_participants >= 2 and \
               log(number_participants, 2).is_integer() and \
               cls.state_machine[chat_id]["state"] == "registration"

    @classmethod
    async def handle_state_in_chat(cls, update) -> Optional[tuple[str, str]]:
        payload = update["object"]["payload"]["button"]
        chat_id = update["object"]["peer_id"]

        if chat_id not in cls.state_machine:
            cls.state_machine[chat_id] = {"state": "registration", "id_participants": {}, "game_tree": None}

        if payload == "reg_but":
            await cls.registration_user(update)

        if payload == "start_but":
            if await cls.ready_to_start(update):
                cls.state_machine[chat_id]["game_tree"] = GameTree(list(cls.state_machine[chat_id][
                                                                            "id_participants"].values()))
                await cls.state_machine[chat_id]["game_tree"].start()
                cls.state_machine[chat_id]["state"] = "started"

                return cls.state_machine[chat_id]["game_tree"].photo_ids_current_pair

        if cls.state_machine[chat_id]["state"] == "started":
            if payload == "first_but" or payload == "second_but":
                await cls.state_machine[chat_id]["game_tree"].set_vote_for_current_pair(payload == "first_but")

        if payload == "next_but":
            await cls.state_machine[chat_id]["game_tree"].next_pair()

            photo_ids = cls.state_machine[chat_id]["game_tree"].photo_ids_current_pair
            if len(photo_ids) == 1:
                cls.state_machine[chat_id]["state"] = "registration"
                cls.state_machine[chat_id]["id_participants"].clear()
                cls.state_machine[chat_id]["game_tree"] = None
            return photo_ids

    @classmethod
    def make_keyboard_registered(cls):
        return {
            "one_time": False,
            "buttons":
                [
                    [cls.build_button(label="Зарегистрироваться на игру",
                                      color="primary",
                                      payload="{\"button\": \"reg_but\"}"),
                     cls.build_button(label="Начать игру",
                                      color="secondary",
                                      payload="{\"button\": \"start_but\"}")
                     ],
                    [cls.build_button(label="Следующий раунд",
                                      color="positive",
                                      payload="{\"button\": \"next_but\"}")
                     ]
                ]
        }

    @classmethod
    def make_message_keyboard(cls):
        return {
            "inline": True,
            "buttons":
                [
                    [cls.build_button(label="Левый",
                                      color="positive",
                                      payload="{\"button\": \"first_but\"}"),
                     cls.build_button(label="Правый",
                                      color="negative",
                                      payload="{\"button\": \"second_but\"}")
                     ],
                ]
        }

    async def handle_updates(self, message: AbstractIncomingMessage):
        async with message.process():
            keyboard_body = self.make_keyboard_registered()
            message_keyboard = self.make_message_keyboard()
            raw_data = json.loads(message.body.decode())
            for update in raw_data:
                queue = await self.rabbit_channel.declare_queue(
                    "task_queue_3",
                    durable=True,
                )
                if update["type"] == "message_event":
                    new_message_body = {
                        "user_id": update["object"]["user_id"],
                        "peer_id": update["object"]["peer_id"],
                        "keyboard": json.dumps(keyboard_body),
                        "text": "hello"
                    }
                    photo_ids = await self.handle_state_in_chat(update)

                    if photo_ids is not None:
                        if len(photo_ids) == 2:
                            new_message_body["photo_id"] = ("photo" + photo_ids[0], "photo" + photo_ids[1])
                            new_message_body["text"] = "Голосуем"
                            new_message_body["keyboard"] = json.dumps(message_keyboard)
                        elif len(photo_ids) == 1:
                            new_message_body["photo_id"] = ("photo" + photo_ids[0])
                            new_message_body["text"] = "ПОБЕДИТЕЛЬ!!!!"

                    await self.rabbit_channel.default_exchange.publish(
                        Message(
                            json.dumps(new_message_body).encode(),
                            delivery_mode=DeliveryMode.PERSISTENT,
                        ),
                        routing_key="task_queue_3",
                    )

                if update["type"] == "message_new":
                    new_message_body = {
                        "user_id": update["object"]["message"]["from_id"],
                        "text": update["object"]["message"]["text"],
                        "peer_id": update["object"]["message"]["peer_id"],
                        "keyboard": json.dumps(keyboard_body),
                    }

                    await self.rabbit_channel.default_exchange.publish(
                        Message(
                            json.dumps(new_message_body).encode(),
                            delivery_mode=DeliveryMode.PERSISTENT,
                        ),
                        routing_key="task_queue_3",
                    )


def run_manager():
    bot = BotManager()
    asyncio.run(bot.start())


if __name__ == "__main__":
    run_manager()
