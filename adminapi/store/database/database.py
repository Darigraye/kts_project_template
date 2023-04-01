from typing import TYPE_CHECKING, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

if TYPE_CHECKING:
    from adminapi.web.app import Application

from adminapi.store.database import db

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

    async def connect(self, *_, **__):
        self._db = db
        url_to_connect: str = self._build_url_to_connect(
            username=self.app.config.database.user,
            password=self.app.config.database.password,
            database=self.app.config.database.database
        )
        self._engine = create_async_engine(url_to_connect, echo=True, future=True)
        self.session = sessionmaker(self._engine, expire_on_commit=False, future=True, class_=AsyncSession)

    async def disconnect(self, *_, **__):
        if self._engine:
            await self._engine.dispose()
