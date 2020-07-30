from handlers.login import Login
from handlers.logout import Logout
from handlers.recipes import Recipes
from handlers.users import Users, UsersMe, UsersID


async def init_handlers(app):
    cors = app["cors"]
    cors.add(app.router.add_route("*", "/users", Users))
    cors.add(app.router.add_route("*", "/users/@me", UsersMe))
    cors.add(app.router.add_route("*", r"/users/{id}", UsersID))
    cors.add(app.router.add_route("*", "/login", Login))
    cors.add(app.router.add_route("*", "/logout", Logout))
    cors.add(app.router.add_route("*", "/recipes", Recipes))
