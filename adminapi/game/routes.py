from typing import TYPE_CHECKING

from adminapi.game.views import (GetLatestGameView,
                                 GetAllGamesView,
                                 GetAllUserGames,
                                 DeleteGamesInChatView,
                                 ClearDatabaseView)

if TYPE_CHECKING:
    from adminapi.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.latest", GetLatestGameView)
    app.router.add_view("/game.all", GetAllGamesView)
    app.router.add_view("/game.all_of_user", GetAllUserGames)
    app.router.add_view("/game.delete_games", DeleteGamesInChatView)
    app.router.add_view("/game.clear_database", ClearDatabaseView)
