from typing import Sequence, Callable, Optional

from aiohttp.web import (
    Application as AiohttpApplication,
    View as AiohttpView,
    Request as AiohttpRequest,
)

# from pyparsing import Optional

# from kts_backend import __appname__, __version__
from kts_backend.store import setup_store, Store
from kts_backend.store.database import Database
from .config import setup_config, Config
from .mw import setup_middlewares

from .urls import register_urls


# __all__ = ("Application", )


class Application(AiohttpApplication):
    config: Optional[Config] = None
    store: Optional[Store] = None
    database: Optional[Database] = None


app = Application()


def setup_app(config_path: str) -> Application:
    setup_config(app, config_path)
    setup_middlewares(app)
    setup_store(app)
    return app
