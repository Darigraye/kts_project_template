from sqlalchemy import select, desc

from adminapi.base.base_accessor import BaseAccessor
from kts_backend.games.game_dataclasses import Game, GameScore
from kts_backend.games.models import GameModel, GameScoreModel
from kts_backend.users.user_dataclasses import Player


class GameAccessor(BaseAccessor):
    async def get_latest_game(self, chat_id):
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

    async def get_all_games(self, chat_id: int) -> list[Game]:
        select_query = (
            select(GameModel)
                .join(GameModel.players)
                .join(GameScoreModel.player)
                .where(GameModel.chat_id == chat_id)
                .order_by(desc(GameModel.created_at))
        )
        async with self.app.database.session() as session:
            res = await session.execute(select_query)

        wrapped_list_data: list[GameModel] = res.scalars()

        return [Game(id=wrapped_data.players[0].game_id,
                     chat_id=chat_id,
                     created_at=wrapped_data.created_at,
                     players=[Player(profile_id=player.player.profile_id,
                                     name=player.player.name,
                                     last_name=player.player.last_name,
                                     score=GameScore(scores=player.scores))
                              for player in wrapped_data.players])
                for wrapped_data in wrapped_list_data]
