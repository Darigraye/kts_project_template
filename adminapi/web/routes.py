from aiohttp.web_app import Application


def setup_routes(app: Application):
    from adminapi.admin.routes import setup_routes as setup_admin_routes
    from adminapi.game.routes import setup_routes as setup_game_routes

    setup_admin_routes(app)
    setup_game_routes(app)