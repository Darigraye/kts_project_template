from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class BaseAccessor:
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app
        app.on_startup.append(self.connect)
        app.on_cleanup.append(self.disconnect)

    async def connect(self, app: "Application"):
        pass

    async def disconnect(self, app: "Application"):
        pass
