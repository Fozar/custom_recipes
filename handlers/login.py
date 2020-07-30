from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import remember

from db_auth import check_credentials


class Login(web.View, CorsViewMixin):
    async def get(self):
        json = await self.request.json()
        if not await check_credentials(**json):
            raise web.HTTPUnauthorized

        response = web.HTTPOk
        await remember(self.request, response, json["login"])
        raise response
