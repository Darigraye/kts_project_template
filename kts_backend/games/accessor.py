from typing import Optional

from sqlalchemy import select, desc

from kts_backend.base import BaseAccessor
from .models import GameModel, GameScoreModel
from .game_dataclasses import Game, GameScore
from kts_backend.users.models import PlayerModel
from kts_backend.users.user_dataclasses import Player


class GameAccessor(BaseAccessor):
    async def add_new_game(self, chat_id: int, players: list[Player]) -> Optional[Game]:
        model_game = GameModel(chat_id=chat_id)

        for player in players:
            model_player = await self.app.store.user.get_player_by_vk_id(player.profile_id)
            if model_player is None:
                model_player = await self.app.store.user.add_new_player(player)
            model_game.player.append(model_player)

        async with self.app.database.session() as session:
            session.add(model_game)
            await session.commit()

        added_model = await self.get_latest_game_by_chat_id(chat_id=chat_id)

        return added_model

    async def get_latest_game_by_chat_id(self, chat_id: int) -> Optional[Game]:
        select_query = select(GameModel, GameScoreModel.scores, PlayerModel).join(GameModel.players).join(
            GameScoreModel.player_id).where(GameModel.chat_id == chat_id).order_by(
            desc(GameModel.created_at))

        async with self.app.database.session() as session:
            res = await session.execute(select_query)

        wrapped_data = res.scalars().all()
        if wrapped_data:
            processed_players = [Player(profile_id=data.profile_id,
                                        name=data.name,
                                        last_name=data.last_name,
                                        score=GameScore(scores=data.scores))
                                 for data in wrapped_data]

            return Game(id=wrapped_data[0].id,
                        created_at=wrapped_data[0].created_at,
                        chat_id=wrapped_data[0].chat_id,
                        players=processed_players)
        return None
