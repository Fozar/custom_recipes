from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import check_authorized, permits

from models import User, Recipe, CookingStep


class Recipes(web.View, CorsViewMixin):
    async def post(self):
        """Создает новый рецепт"""
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        user = await User.get(pk=user_id)

        json = await self.request.json()

        try:
            steps = json.pop("cooking_steps")
        except KeyError:
            raise web.HTTPBadRequest

        recipe = await Recipe.create(author=user, **json)

        for i, step in enumerate(steps):
            await CookingStep.create(recipe=recipe, order=i + 1, **step)
        raise web.HTTPCreated(
            headers={"Location": str(self.request.url / str(recipe.id))}
        )
