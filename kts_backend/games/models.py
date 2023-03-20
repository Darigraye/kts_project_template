from typing import List

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped

from kts_backend.store.database import db
from kts_backend.users.models import PlayerModel


class GameScoreModel(db):
    __tablename__ = 'game_score'

    game_id = Column(Integer, ForeignKey('game.id', ondelete='CASCADE'), primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id', ondelete='CASCADE'), primary_key=True)
    scores = Column(Integer, nullable=False)
    player: Mapped["PlayerModel"] = relationship()


class GameModel(db):
    __tablename__ = 'game'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_id = Column(Integer, nullable=False)
    players: Mapped[List[GameScoreModel]] = relationship()
