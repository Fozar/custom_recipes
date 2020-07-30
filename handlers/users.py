from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import remember, check_authorized, permits
from passlib.apps import custom_app_context as pwd_context

from models import User


class Users(web.View, CorsViewMixin):
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
    @staticmethod
    async def get_user_profile(user_id: int):
        user = await User.get(pk=user_id)
        await user.fetch_related("recipes")
        return {
            "id": user_id,
            "login": user.login,
            "status": "active",
            "recipe_count": len(user.recipes),
        }

    async def get(self):
        """Возвращает профиль пользователя"""
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        user_id = int(self.request.match_info["id"])
        return web.json_response(await self.get_user_profile(user_id))


class UsersMe(UsersID):  # Наследует от UsersID
    async def get(self):
        """Возвращает профиль авторизированного пользователя"""
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        return web.json_response(await self.get_user_profile(user_id))
