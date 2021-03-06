from json import JSONDecodeError

from aiohttp import web
from aiohttp_cors import CorsViewMixin
from aiohttp_security import remember, check_authorized, permits, forget
from passlib.apps import custom_app_context as pwd_context
from tortoise.exceptions import IntegrityError, IncompleteInstanceError
from tortoise.functions import Count

from models import User


class Users(web.View, CorsViewMixin):
    async def get(self):
        """Возвращает список пользователей, отсортированный по кол-ву рецептов.
        По умолчанию первые 10.
        """
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        try:
            limit = int(self.request.query.get("limit", "10"))
        except ValueError:
            limit = 10
        users = (
            await User.all()
            .annotate(recipes_count=Count("recipes"))
            .order_by("-recipes_count")
            .limit(limit)
        )
        return web.json_response([await user.to_dict() for user in users])

    async def post(self):
        """Создает нового пользователя"""
        try:
            json = await self.request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

        try:
            if await User.exists(login=json["login"]):
                raise web.HTTPConflict  # Пользователь с таким именем уже существует

            json["password_hash"] = pwd_context.hash(json.pop("password"))
        except KeyError:
            raise web.HTTPBadRequest

        try:
            user = await User.create(**json)
        except (IntegrityError, IncompleteInstanceError) as e:
            raise web.HTTPBadRequest(reason=str(e))

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

        user_id_str = self.request.match_info["id"]
        if user_id_str == "@me":
            user_id = int(await check_authorized(self.request))
        else:
            try:
                user_id = int(user_id_str)
            except ValueError:
                raise web.HTTPBadRequest
        user = await User.get_or_none(pk=user_id)
        if not user:
            raise web.HTTPNotFound
        return web.json_response(await user.to_dict())

    async def put(self):
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        if self.request.match_info["id"] != "@me":
            if not await permits(self.request, "is_admin"):
                raise web.HTTPForbidden

            try:
                user_id = int(self.request.match_info["id"])
            except ValueError:
                raise web.HTTPBadRequest
        else:
            user_id = int(await check_authorized(self.request))
        try:
            json = await self.request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

        try:
            if await User.filter(login=json["login"]).exists():
                raise web.HTTPConflict
        except KeyError:
            raise web.HTTPBadRequest

        q = await User.filter(pk=user_id).update(login=json["login"])
        if not q:
            raise web.HTTPNotFound

        raise web.HTTPNoContent

    async def delete(self):
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        if self.request.match_info["id"] != "@me":
            if not await permits(self.request, "is_admin"):
                raise web.HTTPForbidden

            try:
                user_id = int(self.request.match_info["id"])
            except ValueError:
                raise web.HTTPBadRequest
        else:
            user_id = int(await check_authorized(self.request))

        user = await User.get_or_none(pk=user_id)
        if not user:
            raise web.HTTPNotFound

        if user.login == self.request.app["config"]["superuser"]["login"]:
            raise web.HTTPForbidden

        response = web.HTTPNoContent
        await forget(self.request, web.HTTPNoContent)
        await user.delete()
        raise response


class UsersIDStatus(web.View, CorsViewMixin):
    async def patch(self):
        """Устанавливает статус пользователя"""
        if not await permits(self.request, "is_admin"):
            raise web.HTTPForbidden

        user_id_str = self.request.match_info["id"]
        if user_id_str == "@me":
            user_id = int(await check_authorized(self.request))
        else:
            try:
                user_id = int(user_id_str)
            except ValueError:
                raise web.HTTPBadRequest

        try:
            json = await self.request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

        try:
            if json["status"] == "active":
                status = True
            elif json["status"] == "blocked":
                status = False
            else:
                raise web.HTTPBadRequest
        except KeyError:
            raise web.HTTPBadRequest
        query = await User.filter(pk=user_id).update(is_active=status)
        if not query:
            raise web.HTTPNotFound

        raise web.HTTPNoContent


class UsersIDFavorites(web.View, CorsViewMixin):
    async def get(self):
        if not await permits(self.request, "is_active"):
            raise web.HTTPForbidden

        user_id_str = self.request.match_info["id"]
        if user_id_str == "@me":
            user_id = int(await check_authorized(self.request))
        else:
            try:
                user_id = int(user_id_str)
            except ValueError:
                raise web.HTTPBadRequest
        user = await User.get_or_none(pk=user_id)
        if not user:
            raise web.HTTPNotFound

        await user.fetch_related("favorites")

        return web.json_response(
            [await recipe.to_dict() for recipe in list(user.favorites)]
        )
