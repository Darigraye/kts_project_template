import asyncio
import json
import os
import sys
from time import time

from math import log
from asyncio import Future
from typing import TYPE_CHECKING, Optional

from aio_pika import connect, Message
from aio_pika.abc import AbstractIncomingMessage, DeliveryMode
from aiohttp import ClientSession, TCPConnector

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from kts_backend.web.config import config_from_yaml
from kts_backend.web.utils import build_query, Timer
from kts_backend.games.game_tree import GameTree
from kts_backend.games.game_dataclasses import Game, GameScore
from kts_backend.users.user_dataclasses import Player, GameScore

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class BotManager:
    state_machine: dict[int, dict[str, Optional[str | dict[int, tuple[str, int]] | GameTree | int]]] = {}

    def __init__(self, app: "Application"):
        self.app = app
        app.on_startup.append(self.start)
        self.rabbit_connect = None
        self.rabbit_channel = None

    async def start(self, *args, **kwargs):
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

    async def registration_user(self, update) -> str:
        chat_id = update["object"]["peer_id"]
        user_id = update["object"]["user_id"]
        res_text = "Вы успешно зарегистрированы"

        photo_id, first_name, last_name = await self.app.store.game.get_photo_id(user_id)

        if user_id in self.state_machine[chat_id]["id_participants"]:
            res_text = "Вы уже зарегистрированы"

        if photo_id is None:
            res_text = "Добавьте аватарку"

        self.state_machine[chat_id]["id_participants"][user_id] = (photo_id, first_name, last_name)
        return res_text

    @classmethod
    async def ready_to_start(cls, update) -> bool:
        chat_id = update["object"]["peer_id"]
        number_participants = len(cls.state_machine[chat_id]["id_participants"])

        return number_participants >= 2 and \
               log(number_participants, 2).is_integer() and \
               cls.state_machine[chat_id]["state"] == "registration"

    async def handle_state_in_chat(self, update) -> dict[str, Optional[tuple[str, str] | str]]:
        payload = update["object"]["payload"]["button"]
        chat_id = update["object"]["peer_id"]
        user_id = update["object"]["user_id"]

        event_text = "Ничего не произошло"
        photo_ids = None
        info_text = None
        owners_name = []

        if chat_id not in self.state_machine:
            self.state_machine[chat_id] = {"state": "registration",
                                           "id_participants": {},
                                           "game_tree": None,
                                           "timer": None,
                                           }

        if payload == "reg_but":
            event_text = await self.registration_user(update)

        if payload == "start_but":
            if user_id not in self.state_machine[chat_id]["id_participants"]:
                event_text = "Вы не зарегистрированы на игру!"

            if await self.ready_to_start(update):
                self.state_machine[chat_id]["game_tree"] = GameTree(list(self.state_machine[chat_id][
                                                                             "id_participants"].values()))
                players = [Player(profile_id=id_participant,
                                  name=info_participant[1],
                                  last_name=info_participant[2],
                                  score=GameScore(scores=0)) for id_participant, info_participant in
                           self.state_machine[chat_id]["id_participants"].items()]
                await self.app.store.game.add_new_game(chat_id=chat_id, players=players)
                await self.state_machine[chat_id]["game_tree"].start()
                self.state_machine[chat_id]["state"] = "started"

                event_text = "Вы начали игру!"
                cur_pair = self.state_machine[chat_id]["game_tree"].current_pair
                photo_ids = [node.photo_id for node in cur_pair]
                owners_name = [node.owner_name for node in cur_pair]
            else:
                event_text = "Новую игру начать нельзя (недостаточное количество игроков / игра уже начата)"

        if self.state_machine[chat_id]["state"] == "started":
            if payload == "first_but" or payload == "second_but":
                await self.state_machine[chat_id]["game_tree"].set_vote_for_current_pair(payload == "first_but")

                event_text = "Вы проголосовали"

        if payload == "next_but":
            if user_id not in self.state_machine[chat_id]["id_participants"]:
                event_text = "Вы не зарегистрированы на игру!"

            if self.state_machine[chat_id]["state"] == "started":
                winner = await self.state_machine[chat_id]["game_tree"].next_pair()
                await self.app.store.game.update_user_score(vk_id=int(winner.owner_id),
                                                            scores=winner.number_votes,
                                                            chat_id=chat_id)

                cur_pair = self.state_machine[chat_id]["game_tree"].current_pair
                photo_ids = [node.photo_id for node in cur_pair]
                owners_name = [node.owner_name for node in cur_pair]
                if len(photo_ids) == 1:
                    self.state_machine[chat_id]["state"] = "registration"
                    self.state_machine[chat_id]["id_participants"].clear()
                    self.state_machine[chat_id]["game_tree"] = None
                event_text = "Вы решили, что нам нужно двигаться к следующей паре"
            else:
                event_text = "Игра не начата"

        if payload == "info_but":
            game = await self.app.store.game.get_latest_game_by_chat_id(chat_id)

            if game is None:
                info_text = "Ни одной игры ещё не было сыграно!"
            else:
                if self.state_machine[chat_id]["state"] == "started":
                    info_text = f"Информация о текущей игре: дата и время начала - {game.created_at}"
                else:
                    info_text = f"Инфмормация о последней сыгранной игре: %0A дата и время начала - {game.created_at} %0A"
                players_info = "Информация об игроках: %0A "
                for player in game.players:
                    players_info += f"%0AИмя: {player.name}, Фамилия: {player.last_name}, Количество набранных" \
                                    f"очков: {player.score.scores} %0A"
                info_text += players_info
        return {"event_text": event_text,
                "users": {"photo_ids": photo_ids, "names": owners_name},
                "info_text": info_text}

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
                     ],
                    [cls.build_button(label="Информация об игре",
                                      color="primary",
                                      payload="{\"button\": \"info_but\"}")

                    ]
                ]
        }

    @classmethod
    def make_message_keyboard(cls, left, right):
        return {
            "inline": True,
            "buttons":
                [
                    [cls.build_button(label=left,
                                      color="positive",
                                      payload="{\"button\": \"first_but\"}"),
                     cls.build_button(label=right,
                                      color="negative",
                                      payload="{\"button\": \"second_but\"}")
                     ],
                ]
        }

    async def handle_updates(self, message: AbstractIncomingMessage):
        async with message.process():
            raw_data = json.loads(message.body.decode())
            keyboard_body = self.make_keyboard_registered()
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
                        "text": "hello",
                        "event_id": update["object"]["event_id"],
                    }
                    handle_res = await self.handle_state_in_chat(update)

                    photo_ids = handle_res["users"].get("photo_ids")
                    info_text = handle_res.get("info_text")

                    if handle_res.get("event_text"):
                        new_message_body["event_text"] = handle_res["event_text"]

                    if info_text:
                        new_message_body["text"] = info_text

                    if photo_ids is not None:
                        if len(photo_ids) == 2:
                            message_keyboard = self.make_message_keyboard(left=handle_res["users"]["names"][0],
                                                                          right=handle_res["users"]["names"][1])
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
