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
SECRET_KEY=django-insecure-ocn%a0d4&o#9)-9(k#+^9#i3*ck@1t^+%n$4bef#_iwt1nb5c&
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DEBUG=False
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

# Технологии

![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)

### Доступы:


```
|    Адрес                 |     Описание            |
|127.0.0.1:8000            | Главная страница        |
|127.0.0.1:8000/admin      | Админка                 |
|127.0.0.1:8000/api/docs/  | Документация к API      |

```
Вместо 127.0.0.1 можно использовать localhost

### Автор
Шведуненко Денис
shvedunenkodenis@gmail.com
