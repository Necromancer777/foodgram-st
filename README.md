# Foodgram

## Описание проекта
«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.

## Запуск проекта

Создать файл .env в корневой директории проекта, например:


```.env
POSTGRES_USER=django
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_DB=django
DB_HOST=db
DB_PORT=5432
SECRET_KEY=django-insecure-ocn%a0d4&o#9)-9(k#+^9#i3*ck@1t^+%n$4bef#_iwt1nb5c&   # Пример
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
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

```bash
docker compose exec backend python manage.py collectstatic
```

Загрузить в базу ингридиенты:

```bash
docker compose exec backend python manage.py load_ingredients
```
