from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import remember, check_authorized, permits
from passlib.apps import custom_app_context as pwd_context
from tortoise.functions import Count

from models import User


class Users(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает список пользователей, отсортированный по кол-ву рецептов.
        По умолчанию первые 10.
        """
        limit = int(self.request.query.get("limit", "10"))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        users = (
            await User.all()
            .annotate(recipes_count=Count("recipes"))
            .order_by("-recipes_count")
            .limit(limit)
        )
        return web.json_response([await user.get_profile() for user in users])

    async def post(self):
        """Создает нового пользователя"""
        json = await self.request.json()
        try:
            if await User.exists(login=json["login"]):
                raise web.HTTPBadRequest  # Пользователь с таким именем уже существует
        except KeyError:
            raise web.HTTPBadRequest

        json["password_hash"] = pwd_context.hash(json.pop("password"))
        user = await User.create(**json)
        response = web.HTTPCreated(
            headers={"Location": str(self.request.url / str(user.id))}
        )
        await remember(self.request, response, str(user.id))
        raise response


class UsersID(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает профиль пользователя"""
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        user_id = int(self.request.match_info["id"])
        user = await User.get(pk=user_id)
        return web.json_response(await user.get_profile())


class UsersMe(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает профиль авторизированного пользователя"""
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        user = await User.get(pk=user_id)
        return web.json_response(await user.get_profile())
