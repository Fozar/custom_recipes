from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import remember, check_authorized, permits
from passlib.apps import custom_app_context as pwd_context

from models import User as UserModel


class Users(web.View, CorsViewMixin):
    async def post(self):
        """Создает нового пользователя"""
        json = await self.request.json()
        try:
            if await UserModel.exists(login=json["login"]):
                raise web.HTTPBadRequest  # Пользователь с таким именем уже существует
        except KeyError:
            raise web.HTTPBadRequest

        json["password_hash"] = pwd_context.hash(json.pop("password"))
        user = await UserModel.create(**json)
        response = web.HTTPCreated(
            headers={"Location": str(self.request.url / str(user.id))}
        )
        await remember(self.request, response, str(user.id))
        raise response


class UsersMe(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает профиль авторизированного пользователя"""
        user_id = int(await check_authorized(self.request))
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        user = await UserModel.get(pk=user_id)
        await user.fetch_related("recipes")
        return web.json_response(
            {"id": user_id, "login": user.login, "status": "active", "recipe_count": len(user.recipes)}
        )
