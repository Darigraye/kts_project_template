from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
)

from kts_backend.store.database import db


class PlayerModel(db):
    __tablename__ = "player"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
