from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to="users/",
        blank=True,
        null=True,
        default=None,
        verbose_name="Аватар пользователя",
    )

    email = models.EmailField("Адрес электронной почты", max_length=254,
                              unique=True)

    username_validator = RegexValidator(
        regex=r"^[\w-]+$",
    )

    username = models.CharField(
        "Юзернейм",
        max_length=150,
        unique=True,
        validators=[username_validator],
    )

    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]

    def __str__(self):
        return self.username


class Subscription(models.Model):
    follower = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="subscribers",
    )

    class Meta:
        verbose_name = "подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "author"], name="unique_subscription"
            )
        ]

    def __str__(self):
        return f"{self.follower} подписан на {self.author}"
