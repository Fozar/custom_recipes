from aiohttp_security import AbstractAuthorizationPolicy

from models import User


class DBAuthorizationPolicy(AbstractAuthorizationPolicy):
    async def authorized_userid(self, identity):
        if User.exists(id=int(identity)):
            return identity
        else:
            return None

    async def permits(self, identity, permission, context=None):
        if identity is None:
            return False

        user = await User.get_or_none(id=int(identity))
        if user is None:
            return False

        return getattr(user, permission, True)


async def check_credentials(login: str, password: str):
    user = await User.get_or_none(login=login)
    if user is None:
        return False

    return user.verify_password(password)
