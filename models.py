from enum import IntEnum
from passlib.apps import custom_app_context as pwd_context

from tortoise import Model, fields


class DishType(IntEnum):
    SALAD = 0  # салат
    FIRST_COURSE = 1  # первое
    SECOND_COURSE = 2  # второе
    SOUP = 3  # суп
    DESSERT = 4  # десерт
    DRINK = 5  # напиток


class User(Model):
    id = fields.IntField(pk=True)
    login = fields.CharField(max_length=100, unique=True, description="никнейм")
    password_hash = fields.CharField(max_length=255, description="пароль")
    is_admin = fields.BooleanField(default=False, description="админ")
    is_active = fields.BooleanField(default=True, description="статус")
    favorites = fields.ManyToManyField(
        "models.Recipe",
        related_name="users",
        null=True,
        through="favorites",
        description="избранные рецепты",
    )
    recipes: fields.ReverseRelation["Recipe"]

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.password_hash)

    async def get_profile(self):
        await self.fetch_related("recipes")
        return {
            "id": self.id,
            "login": self.login,
            "status": "active",
            "recipe_count": len(self.recipes),
        }


class Recipe(Model):
    author = fields.ForeignKeyField(
        "models.User", related_name="recipes", description="автор (пользователь)"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="дата создания")
    name = fields.CharField(max_length=100, description="название")
    description = fields.TextField(description="описание")
    final_dish_photo = fields.TextField(
        description="фотография конечного блюда (ссылка)", null=True
    )
    dish_type = fields.IntEnumField(enum_type=DishType, description="тип блюда")
    is_active = fields.BooleanField(default=True, description="статус")
    likes = fields.ManyToManyField(
        "models.User",
        through="likes",
        related_name="likes",
        description="лайки",
        null=True,
    )
    hashtags = fields.ManyToManyField(
        "models.Hashtag",
        related_name="recipes",
        description="набор хештегов",
        null=True,
    )


class CookingStep(Model):
    recipe = fields.ForeignKeyField(
        "models.Recipe", related_name="cooking_steps", description="рецепт"
    )
    order = fields.IntField(description="порядок, номер шага")
    text = fields.TextField(description="текст, описание")
    photo = fields.TextField(null=True, description="фотография (ссылка)")


class Hashtag(Model):
    name = fields.CharField(max_length=100, description="имя хештега")
