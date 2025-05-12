# Foodgram

## Описание проекта
«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.

## Запуск проекта

Создать файл .env в корневой директории проекта, например:


```.env
SECRET_KEY="..."                      # Находится в settings.py
DB_ENGINE=django.db.backends.postgres # Тип базы данных (postgres)
DB_NAME=postgres                      # Имя базы
POSTGRES_USER=postgres                # Логин для подключения к БД
POSTGRES_PASSWORD=password            # Пароль для подключения к БД
DB_HOST=db                            # Название контейнера с БД
DB_PORT=5432                          # Порт для подключения к БД
```

Запустить docker compose:

```bash
docker compose up --build
```

Выполнить миграции внутри БД:

```bash
docker compose exec backend python manage.py migrate
```

Загрузить статику:

- Загрузите статику

```bash
docker compose exec backend python manage.py collectstatic
```

Загрузить в базу ингридиенты:

```bash
docker compose exec backend python manage.py load_ingredients
```
