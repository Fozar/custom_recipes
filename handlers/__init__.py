from handlers.login import Login
from handlers.logout import Logout
from handlers.users import Users


async def init_handlers(app):
    cors = app["cors"]
    cors.add(app.router.add_route("*", "/users", Users))
    cors.add(app.router.add_route("*", "/login", Login))
    cors.add(app.router.add_route("*", "/logout", Logout))
