from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import is_anonymous, forget


class Logout(web.View, CorsViewMixin):
    async def get(self):
        if await is_anonymous(self.request):
            raise web.HTTPUnauthorized

        response = web.HTTPOk
        await forget(self.request, response)

        raise response
