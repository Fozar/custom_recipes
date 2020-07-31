import asyncio
import json

from aiohttp import web
from aiohttp_cors import setup as setup_cors, ResourceOptions
from aiohttp_security import setup as setup_security, SessionIdentityPolicy
from aiohttp_session import setup as setup_session, SimpleCookieStorage
from tortoise import Tortoise

from db_auth import DBAuthorizationPolicy
from handlers import init_handlers

try:
    import uvloop
except ImportError:
    uvloop = None  # Windows
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def init_db(app):
    await Tortoise.init(
        db_url=app["config"]["db_url"], modules={"models": ["models"]},
    )
    await Tortoise.generate_schemas()


def main():
    app = web.Application()
    with open("config.json", "r") as f:
        config = json.load(f)
    app["config"] = config
    cors = setup_cors(
        app,
        defaults={
            "*": ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*",
            )
        },
    )
    app["cors"] = cors
    setup_session(app, SimpleCookieStorage())
    setup_security(app, SessionIdentityPolicy(), DBAuthorizationPolicy())
    app.on_startup.append(init_db)
    app.on_startup.append(init_handlers)
    web.run_app(app, host="localhost", port=5000)


if __name__ == "__main__":
    main()
