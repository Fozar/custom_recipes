from handlers.login import Login
from handlers.logout import Logout
from handlers.recipes import (
    Recipes,
    RecipeID,
    RecipeIDStatus,
    RecipeIDLike,
    RecipeIDFavorite,
)
from handlers.users import Users, UsersID, UsersIDStatus


async def init_handlers(app):
    cors = app["cors"]
    cors.add(app.router.add_route("*", "/users", Users))
    cors.add(app.router.add_route("*", r"/users/{id}", UsersID))
    cors.add(app.router.add_route("*", r"/users/{id}/status", UsersIDStatus))
    cors.add(app.router.add_route("*", "/login", Login))
    cors.add(app.router.add_route("*", "/logout", Logout))
    cors.add(app.router.add_route("*", "/recipes", Recipes))
    cors.add(app.router.add_route("*", r"/recipes/{id}", RecipeID))
    cors.add(app.router.add_route("*", r"/recipes/{id}/status", RecipeIDStatus))
    cors.add(app.router.add_route("*", r"/recipes/{id}/like", RecipeIDLike))
    cors.add(app.router.add_route("*", r"/recipes/{id}/favorite", RecipeIDFavorite))
