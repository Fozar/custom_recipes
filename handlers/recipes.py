from contextlib import suppress
from json.decoder import JSONDecodeError

from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import check_authorized, permits
from tortoise.exceptions import FieldError
from tortoise.expressions import F
from tortoise.transactions import in_transaction

from models import User, Recipe, CookingStep, DishType


class Recipes(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает список рецептов"""
        await check_authorized(self.request)
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
        try:
            json = await self.request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

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


class RecipesID(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает рецепт"""
        await check_authorized(self.request)
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        try:
            recipe = await Recipe.get_or_none(
                pk=int(self.request.match_info["recipe_id"])
            )
        except ValueError:
            raise web.HTTPBadRequest

        if not recipe:
            raise web.HTTPNotFound

        return web.json_response(await recipe.to_dict(False))

    async def put(self):
        """Изменяет рецепт"""
        user_id = await check_authorized(self.request)
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        try:
            recipe = await Recipe.get_or_none(
                pk=int(self.request.match_info["recipe_id"])
            )
        except ValueError:
            raise web.HTTPBadRequest

        if not recipe:
            raise web.HTTPNotFound

        await recipe.fetch_related("author")
        if recipe.author.id != int(user_id):
            raise web.HTTPForbidden

        try:
            recipe = recipe.update_from_dict(await self.request.json())
        except JSONDecodeError:
            raise web.HTTPBadRequest

        await recipe.save()
        raise web.HTTPNoContent

    async def delete(self):
        """Удаляет рецепт"""
        user_id = await check_authorized(self.request)
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        try:
            recipe = await Recipe.get_or_none(
                pk=int(self.request.match_info["recipe_id"])
            )
        except ValueError:
            raise web.HTTPBadRequest

        if not recipe:
            raise web.HTTPNotFound

        await recipe.fetch_related("author")
        if recipe.author.id != int(user_id):
            raise web.HTTPForbidden

        await recipe.delete()
        raise web.HTTPNoContent


class RecipesIDStatus(web.View, CorsViewMixin):
    async def patch(self):
        """Устанавливает статус рецепта"""
        await check_authorized(self.request)
        if not await permits(self.request, "is_admin"):
            raise web.HTTPForbidden

        try:
            recipe_id = int(self.request.match_info["recipe_id"])
        except ValueError:
            raise web.HTTPBadRequest
        try:
            json = await self.request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

        if json["status"] == "active":
            status = True
        elif json["status"] == "blocked":
            status = False
        else:
            raise web.HTTPBadRequest
        query = await Recipe.filter(pk=recipe_id).update(is_active=status)
        if not query:
            raise web.HTTPNotFound

        raise web.HTTPNoContent


class RecipesIDLike(web.View, CorsViewMixin):
    async def get_recipe(self):
        try:
            recipe = await Recipe.get_or_none(
                pk=int(self.request.match_info["recipe_id"])
            )
        except ValueError:
            raise web.HTTPBadRequest

        if not recipe:
            raise web.HTTPNotFound

        return recipe

    async def get_user(self):
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        return await User.get(pk=user_id)

    async def put(self):
        """Добавляет лайк"""
        user = await self.get_user()
        recipe = await self.get_recipe()
        await recipe.likes.add(user)
        raise web.HTTPNoContent

    async def delete(self):
        """Удаляет лайк"""
        user = await self.get_user()
        recipe = await self.get_recipe()
        await recipe.likes.remove(user)
        raise web.HTTPNoContent


class RecipesIDFavorite(web.View, CorsViewMixin):
    async def get_recipe(self):
        try:
            recipe = await Recipe.get_or_none(
                pk=int(self.request.match_info["recipe_id"])
            )
        except ValueError:
            raise web.HTTPBadRequest

        if not recipe:
            raise web.HTTPNotFound

        return recipe

    async def get_user(self):
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        return await User.get(pk=user_id)

    async def put(self):
        """Добавляет рецепт в израбранное"""
        user = await self.get_user()
        recipe = await self.get_recipe()
        await user.favorites.add(recipe)
        raise web.HTTPNoContent

    async def delete(self):
        """Удаляет рецепт из избранного"""
        user = await self.get_user()
        recipe = await self.get_recipe()
        await user.favorites.remove(recipe)
        raise web.HTTPNoContent


class RecipesIDStep(web.View, CorsViewMixin):
    async def post(self):
        """Добавляет этап приготовления"""
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        try:
            recipe = await Recipe.get_or_none(
                pk=int(self.request.match_info["recipe_id"])
            )
        except ValueError:
            raise web.HTTPBadRequest

        if not recipe:
            raise web.HTTPNotFound

        await recipe.fetch_related("author")
        if recipe.author.id != user_id:
            raise web.HTTPForbidden

        try:
            json = await self.request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

        async with in_transaction():
            await CookingStep.filter(recipe=recipe, order__gte=json["order"]).update(
                order=F("order") + 1
            )
            step = await CookingStep.create(recipe=recipe, **json)
        raise web.HTTPCreated(
            headers={"Location": str(self.request.url / str(step.order))}
        )


class RecipesIDStepOrder(web.View, CorsViewMixin):
    async def put(self):
        """Изменяет этап приготовления"""
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        try:
            async with in_transaction():
                recipe = await Recipe.get_or_none(
                    pk=int(self.request.match_info["recipe_id"])
                )
                order = int(self.request.match_info["order"])
                step = await CookingStep.get_or_none(recipe=recipe, order=order).only(
                    "id"
                )
        except ValueError:
            raise web.HTTPBadRequest

        if not recipe or not step:
            raise web.HTTPNotFound

        await recipe.fetch_related("author")
        if recipe.author.id != user_id:
            raise web.HTTPForbidden

        try:
            json = await self.request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

        async with in_transaction():
            if "order" in json:
                if json["order"] < order:
                    await CookingStep.filter(
                        recipe=recipe, order__gte=json["order"], order__lt=order
                    ).update(order=F("order") + 1)
                elif json["order"] > order:
                    await CookingStep.filter(
                        recipe=recipe, order__gt=order, order__lte=json["order"]
                    ).update(order=F("order") - 1)
            await CookingStep.filter(pk=step.pk).update(**json)

        raise web.HTTPNoContent(
            headers={"Location": str(self.request.url / str(json.get("order", order)))}
        )

    async def delete(self):
        """Удаляет этап приготовления"""
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        try:
            async with in_transaction():
                recipe = await Recipe.get_or_none(
                    pk=int(self.request.match_info["recipe_id"])
                )
                order = int(self.request.match_info["order"])
                step = await CookingStep.get_or_none(recipe=recipe, order=order).only(
                    "id"
                )
        except ValueError:
            raise web.HTTPBadRequest

        if not recipe or not step:
            raise web.HTTPNotFound

        await recipe.fetch_related("author")
        if recipe.author.id != user_id:
            raise web.HTTPForbidden

        async with in_transaction():
            await step.delete()
            await CookingStep.filter(recipe=recipe, order__gt=order).update(
                order=F("order") - 1
            )

        raise web.HTTPNoContent()
