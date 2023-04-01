from typing import Optional, TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from kts_backend.store.database.sqlalchemy_database import db

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[AsyncSession] = None

    @staticmethod
    def _build_url_to_connect(
        username: str, password: str, database: str, host: str = "localhost"
    ) -> str:
        return f"postgresql+asyncpg://{username}:{password}@{host}/{database}"

    async def connect(self, *args, **kwargs) -> None:
        self._db = db
        url_to_connect: str = self._build_url_to_connect(
            username=self.app.config.database.user,
            password=self.app.config.database.password,
            database=self.app.config.database.database,
        )
        self._engine = create_async_engine(
            url_to_connect, echo=True, future=True
        )
        self.session = sessionmaker(
            self._engine,
            expire_on_commit=False,
            future=True,
            class_=AsyncSession,
        )

    async def disconnect(self, *args, **kwargs) -> None:
        if self._engine:
            await self._engine.dispose()
