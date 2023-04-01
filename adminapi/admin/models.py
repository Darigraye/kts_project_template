from kts_backend.store.database.sqlalchemy_database import db

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    NUMERIC,
    String,
    PrimaryKeyConstraint,
    TIMESTAMP,
    Text,
    VARCHAR,
)


class AdminModel(db):
    __tablename__ = "admin"

    id = Column("id", Integer, primary_key=True)
    login = Column("login", String, unique=True, nullable=False)
    password = Column("password", String, nullable=False)
