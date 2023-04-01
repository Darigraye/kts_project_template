from typing import TYPE_CHECKING

from adminapi.store.database.database import Database
from adminapi.store.admin.accessor import AdminAccessor
from adminapi.store.game.accessor import GameAccessor

if TYPE_CHECKING:
    from adminapi.web.app import Application


class Store:
    def __init__(self, app: "Application"):

        self.admins = AdminAccessor(app)
        self.games = GameAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
