from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import remember

from db_auth import check_credentials
from models import User


class Login(web.View, CorsViewMixin):
    async def get(self):
        json = await self.request.json()
        if not await check_credentials(**json):
            raise web.HTTPUnauthorized

        response = web.HTTPOk
        user = await User.get(login=json["login"]).only("id")
        await remember(self.request, response, str(user.id))
        raise response
