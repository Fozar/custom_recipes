from aiohttp_security import remember

from models import User
from aiohttp import web
from aiohttp_cors import CorsViewMixin
from passlib.apps import custom_app_context as pwd_context


class Users(web.View, CorsViewMixin):
    async def post(self):
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
