from handlers.login import Login
from handlers.logout import Logout
from handlers.recipes import (
    Recipes,
    RecipesID,
    RecipesIDStatus,
    RecipesIDLike,
    RecipesIDFavorite, RecipesIDStep, RecipesIDStepOrder,
)
from handlers.users import Users, UsersID, UsersIDStatus, UsersIDFavorites


async def init_handlers(app):
    cors = app["cors"]
    cors.add(app.router.add_route("*", "/users", Users))
    cors.add(app.router.add_route("*", "/users/login", Login))
    cors.add(app.router.add_route("*", "/users/logout", Logout))
    cors.add(app.router.add_route("*", r"/users/{id}", UsersID))
    cors.add(app.router.add_route("*", r"/users/{id}/status", UsersIDStatus))
    cors.add(app.router.add_route("*", r"/users/{id}/favorites", UsersIDFavorites))
    cors.add(app.router.add_route("*", "/recipes", Recipes))
    cors.add(app.router.add_route("*", r"/recipes/{recipe_id}", RecipesID))
    cors.add(app.router.add_route("*", r"/recipes/{recipe_id}/status", RecipesIDStatus))
    cors.add(app.router.add_route("*", r"/recipes/{recipe_id}/like", RecipesIDLike))
    cors.add(app.router.add_route("*", r"/recipes/{recipe_id}/favorite", RecipesIDFavorite))
    cors.add(app.router.add_route("*", r"/recipes/{recipe_id}/step", RecipesIDStep))
    cors.add(app.router.add_route("*", r"/recipes/{recipe_id}/step/{order}", RecipesIDStepOrder))
