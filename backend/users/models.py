from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Аватар пользователя'
    )

    email = models.EmailField('Адрес электронной почты', max_length=254,
                              unique=True)
    username = models.CharField('Уникальный юзернейм', max_length=150,
                                unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):

    follower = models.ForeignKey(User, verbose_name='Пользователь',
                                 on_delete=models.CASCADE,
                                 related_name='followers')
    author = models.ForeignKey(User, verbose_name='Автор',
                               on_delete=models.CASCADE,
                               related_name='subscriber')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.follower} подписан на {self.author}'
