from handlers.login import Login
from handlers.logout import Logout
from handlers.recipes import (
    Recipes,
    RecipesID,
    RecipesIDStatus,
    RecipesIDLike,
    RecipesIDFavorite,
)
from handlers.users import Users, UsersID, UsersIDStatus, UsersIDFavorites


async def init_handlers(app):
    cors = app["cors"]
    cors.add(app.router.add_route("*", "/users", Users))
    cors.add(app.router.add_route("*", r"/users/{id}", UsersID))
    cors.add(app.router.add_route("*", r"/users/{id}/status", UsersIDStatus))
    cors.add(app.router.add_route("*", r"/users/{id}/favorites", UsersIDFavorites))
    cors.add(app.router.add_route("*", "/login", Login))
    cors.add(app.router.add_route("*", "/logout", Logout))
    cors.add(app.router.add_route("*", "/recipes", Recipes))
    cors.add(app.router.add_route("*", r"/recipes/{id}", RecipesID))
    cors.add(app.router.add_route("*", r"/recipes/{id}/status", RecipesIDStatus))
    cors.add(app.router.add_route("*", r"/recipes/{id}/like", RecipesIDLike))
    cors.add(app.router.add_route("*", r"/recipes/{id}/favorite", RecipesIDFavorite))
