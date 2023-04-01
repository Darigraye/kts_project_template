from typing import Optional

from sqlalchemy import select

from kts_backend.base import BaseAccessor
from .models import PlayerModel
from .user_dataclasses import Player, User


class UserAccessor(BaseAccessor):
    async def get_player_by_vk_id(
        self, profile_id: int
    ) -> Optional[PlayerModel]:
        async with self.app.database.session() as session:
            select_query = select(PlayerModel).where(
                PlayerModel.profile_id == profile_id
            )
            res = await session.execute(select_query)

        return res.scalar()

    async def get_list_users(self, chat_id: int) -> list[User]:
        response = await self.app.store.vk_api.get_chat_information(chat_id)
        return [
            User(
                profile_id=user["id"],
                name=user["first_name"],
                last_name=user["last_name"],
            )
            for user in response["users"]
        ]

    async def add_new_player(self, player: Player) -> Optional[PlayerModel]:
        model_player = PlayerModel(
            profile_id=player.profile_id,
            name=player.name,
            last_name=player.last_name,
        )
        async with self.app.database.session() as session:
            session.add(model_player)
            await session.commit()

        return model_player
