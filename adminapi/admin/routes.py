from typing import TYPE_CHECKING

from adminapi.admin.views import AdminLoginView, AdminCurrentView, AdminRegistrationView

if TYPE_CHECKING:
    from adminapi.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/admin.register", AdminRegistrationView)
    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
