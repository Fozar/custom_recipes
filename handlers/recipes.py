from contextlib import suppress

from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import check_authorized, permits
from tortoise.exceptions import FieldError

from models import User, Recipe, CookingStep, DishType


class Recipes(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает список рецептов"""
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        rq = self.request.query
        query = Recipe.all().filter(is_active=True)
        # Фильтрация
        if "hashtag" in rq:
            query = query.filter(hashtags__name=rq["hashtag"])
        if "name" in rq:
            query = query.filter(name__icontains=rq["name"])
        if "dish_type" in rq:
            with suppress(AttributeError):
                query = query.filter(dish_type=getattr(DishType, rq["dish_type"]))
        if "author" in rq:
            query = query.filter(author__login=rq["author"])
        if "has_photo" in rq:
            with suppress(ValueError):
                query = query.filter(
                    final_dish_photo__isnull=not bool(int(rq["has_photo"]))
                )

        # Сортировка
        if "order_by" in rq:
            sorts = [v for k, v in rq.items() if k == "order_by"]
            for sort in sorts:
                if sort.startswith("+"):
                    sort = sort[1:]
                with suppress(FieldError):
                    query = query.order_by(sort)

        # Пагинация
        if "offset" in rq:
            with suppress(ValueError):
                query = query.offset(int(rq["offset"]))

        limit = int(rq.get("limit", "10"))
        query = query.limit(limit)

        return web.json_response([await recipe.to_dict() for recipe in await query])

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


class RecipeID(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает рецепт"""
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        recipe_id = int(self.request.match_info["id"])
        recipe = await Recipe.get(pk=recipe_id)
        return web.json_response(await recipe.to_dict(False))
