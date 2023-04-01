import asyncio
import json
import uuid
from typing import Optional, MutableMapping

from aio_pika import connect, Message
from aio_pika.abc import AbstractConnection, AbstractIncomingMessage
from aiohttp import ClientSession, TCPConnector
from sqlalchemy import select, desc, update, and_

from kts_backend.base import BaseAccessor
from .models import GameModel, GameScoreModel
from .game_dataclasses import Game, GameScore
from kts_backend.users.models import PlayerModel
from kts_backend.users.user_dataclasses import Player
from ..web.utils import build_query


class GameAccessor(BaseAccessor):
    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.futures: MutableMapping[str, asyncio.Future] = {}

    async def add_new_game(
            self, chat_id: int, players: list[Player]
    ) -> Optional[Game]:
        model_game = GameModel(chat_id=chat_id)

        for player in players:
            model_player = await self.app.store.user.get_player_by_vk_id(
                player.profile_id
            )
            if model_player is None:
                model_player = await self.app.store.user.add_new_player(player)
            game_score_model = GameScoreModel(scores=0)
            game_score_model.player = model_player
            model_game.players.append(game_score_model)

        async with self.app.database.session() as session:
            session.add(model_game)
            await session.commit()

    async def get_photo_id(self, user_id: int) -> tuple[str, int]:
        loop = asyncio.get_running_loop()
        connection = await connect(
            "amqp://guest:guest@localhost/", loop=loop,
        )
        channel = await connection.channel()
        callback_queue = await channel.declare_queue(exclusive=True)
        await callback_queue.consume(self.on_response, no_ack=True)

        correlation_id = str(uuid.uuid4())
        future = loop.create_future()

        self.futures[correlation_id] = future

        await channel.default_exchange.publish(
            Message(
                str(user_id).encode(),
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=callback_queue.name,
            ),
            routing_key="rpc_queue",
        )
        res: bytes = await future
        res = res.decode()
        res = json.loads(res)
        return res

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        assert message.correlation_id is not None
        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)
    # async def get_photo_id(self, users_id: int) -> tuple[str, int]:
    #     async with ClientSession(connector=TCPConnector(ssl=False)) as session:
    #         request_link = build_query(
    #             host="api.vk.com",
    #             method="/method/users.get",
    #             params={
    #                 "access_token": self.app.config.bot.token,
    #                 "user_ids": users_id,
    #                 "fields": "photo_id"
    #             }
    #         )
    #
    #         async with session.get(request_link) as poll_response:
    #             response = await poll_response.json()
    #
    #     return response["response"][0].get("photo_id"), \
    #            response["response"][0].get("first_name"), \
    #             response["response"][0].get("last_name")

    async def get_all_games_by_chat_id(self, chat_id: int) -> Optional[Game]:
        select_query = (
            select(GameModel)
                .join(GameModel.players)
                .join(GameScoreModel.player)
                .where(GameModel.chat_id == chat_id)
                .order_by(desc(GameModel.created_at)).first()
        )

        async with self.app.database.session() as session:
            res = await session.execute(select_query)

        wrapped_data = res.scalars().all()
        if wrapped_data:
            processed_players = [
                Player(
                    profile_id=data.profile_id,
                    name=data.name,
                    last_name=data.last_name,
                    score=GameScore(scores=data.scores),
                )
                for data in wrapped_data
            ]
            return Game(
                id=wrapped_data[0].id,
                created_at=wrapped_data[0].created_at,
                chat_id=wrapped_data[0].chat_id,
                players=processed_players,
            )

    async def get_latest_game_by_chat_id(self, chat_id: int) -> Optional[Game]:
        select_query = (
            select(GameModel)
                .join(GameModel.players)
                .join(GameScoreModel.player)
                .where(GameModel.chat_id == chat_id)
                .order_by(desc(GameModel.created_at))
        )

        async with self.app.database.session() as session:
            res = await session.execute(select_query)

        wrapped_data: GameModel = res.scalar()
        if wrapped_data:
            return Game(id=wrapped_data.players[0].game_id,
                        chat_id=chat_id,
                        created_at=wrapped_data.created_at,
                        players=[Player(profile_id=player.player.profile_id,
                                        name=player.player.name,
                                        last_name=player.player.last_name,
                                        score=GameScore(scores=player.scores))
                                 for player in wrapped_data.players])

    async def _get_user_id_by_vk_id(self, vk_id: int) -> int:
        select_query = (
            select(PlayerModel.id)
                .where(PlayerModel.profile_id == vk_id)
        )

        async with self.app.database.session() as session:
            res = await session.execute(select_query)

        return res.scalar()

    async def update_user_score(self, vk_id: int, chat_id: int, scores: int):
        player_id = await self._get_user_id_by_vk_id(vk_id)
        game_model = await self.get_latest_game_by_chat_id(chat_id)
        game_id = game_model.id

        update_query = (
            update(GameScoreModel)
                .where(and_(GameScoreModel.player_id == player_id,
                            GameScoreModel.game_id == game_id))
                .values(scores=GameScoreModel.scores + scores)
        )

        async with self.app.database.session() as session:
            await session.execute(update_query)
            await session.commit()
