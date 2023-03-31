from typing import TYPE_CHECKING

from adminapi.game.views import GetLatestGameView, GetAllGamesView

if TYPE_CHECKING:
    from adminapi.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.latest", GetLatestGameView)
    app.router.add_view("/game.all", GetAllGamesView)
