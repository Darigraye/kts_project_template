from typing import Optional

from aio_pika import connect
from aio_pika.abc import AbstractConnection
from aiohttp import ClientSession, TCPConnector
from sqlalchemy import select, desc, update, and_

from kts_backend.base import BaseAccessor
from .models import GameModel, GameScoreModel
from .game_dataclasses import Game, GameScore
from kts_backend.users.models import PlayerModel
from kts_backend.users.user_dataclasses import Player
from ..web.utils import build_query


class GameAccessor(BaseAccessor):
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

    async def get_photo_id(self, users_id: int) -> list[dict[str, str]]:
        async with ClientSession(connector=TCPConnector(ssl=False)) as session:
            request_link = build_query(
                host="api.vk.com",
                method="/method/users.get",
                params={
                    "access_token": self.app.config.bot.token,
                    "user_ids": users_id,
                    "fields": "photo_id"
                }
            )

            async with session.get(request_link) as poll_response:
                response = await poll_response.json()

        return response["response"][0].get("photo_id")

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
            return Game(chat_id=chat_id,
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
