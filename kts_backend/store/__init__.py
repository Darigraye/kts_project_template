from typing import TYPE_CHECKING

from kts_backend.store.database import Database
from kts_backend.users.models import *
from kts_backend.games.models import *
from kts_backend.store.bot.manager import BotManager

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class Store:
    def __init__(self, app: "Application", *args, **kwargs):
        from kts_backend.users.accessor import UserAccessor
        from kts_backend.store.vk_api.accessor import VkApiAccessor
        from kts_backend.games.accessor import GameAccessor

        self.user = UserAccessor(app)
        self.game = GameAccessor(app)
        self.manager = BotManager(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
