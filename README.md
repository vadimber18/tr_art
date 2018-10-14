**Установка и запуск через docker:**

Убедиться, что установлены docker и docker-compose\
Поменять абсолютные пути на свои в следующих местах:\
`docker-compose.yml` строка 12 у меня `/home/tr_art` - папка с репой \
`docker-compose.yml` строка 39\
переименовать `settings_docker.py` в `settings.py`\
`docker-compose up`

Чтобы nginx раздавал статику, из контейнера web (`docker exec -ti art_web1 $SHELL`):\
`./manage.py collectstatic`

Бд можно восстановить из готовой (https://www.dropbox.com/s/88rk7bjglc745sv/db.sql?dl=0) - в ней есть несколько категорий и языков или не восстанавливать, тогда категории и языки нужно создать руками.

Восстановление (нужно добавить строку `COPY db.sql /db.sql` в `docker/postgres/Dockerfile` и поместить сам файл дампа в папку):\
Из под контейнера psql (`docker exec -ti art_psql1 $SHELL`):\
`adduser %username%` (можно поменять в settings.py и docker-compose.yml, у меня 'vadim') \
`sudo -i -u %username%`\
`cd /` \
`psql tr_art < db.sql`

Без восстановления:
Зайти в контейнер web (`docker exec -ti art_web1 $SHELL`), выполнить `./app/tr_art/manage.py migrate`\
Если не получается, закомментить в `urls.py` все, что связано со view (иначе мигрейт не проходит) - 1 импорт и сами урлы, убедиться, что прошла миграция для приложения articles, если не прошла, сделать `makemigrations articles` -> `migrate`\
Потом не забыть раскомментить `urls.py`\
http://127.0.0.1/login/

**Запуск без docker:**\
`which python3`\
`virtualenv ./venv3 -p 'путь к питон3'`\
`source venv3/bin/activate`\
`pip install -r requirements.txt (лежит в docker/web)`\
Переименовать settings_dev.py в `settings.py`\
`./manage.py runserver 127.0.0.1:8003`\
В это случае базу нужно создать руками:\
`create database tr_art owner %username%;`\
`grant all privileges on database tr_art to %username%;`\
Убедиться, что %username% совпадает с юзером базы в `settings.py`\
Далее восстановить из дампа или сделать migrate. Делается все также, как в случае с докером.

Заполнить базу категориями и языками (пример):\
`./manage.py shell`\
`from articles.models import ArtCategory, ArtLanguage`\
`cats = ["Наука", "Юмор", "Политика", "История", "Фантастика"]`\
`langs = ["Русский", "Английский", "Татарский", "Иврит"]`\
`for cat in cats:`\
    `ArtCategory.objects.create(name=cat)`\
`for lang in langs:`\
    `ArtLanguage.objects.create(name=lang)`

**UPDATE**\
Добавил 3 таска для `celery`:
`notify_new_article` - отсылает оповещение всем переводчикам, когда создается новый заказ\
`notify_update_article` - оповещает заказчика, если его заказ приняли или завершили\
`notify_deadline_article` - каждый день (у меня каждую минуту) оповещает переводчиков о заказах, дедлайн которых скоро настанет\
Для докера контейнеры не делал, описываю как запустить без него: \
Установить пакеты для питона(добавил их в requirements.txt):\
`pip install celery`\
`pip install redis`\
`pip install celery[redis]` (мне не понадобилось)\
Установить сам `redis`:\
`wget http://download.redis.io/redis-stable.tar.gz`\
`tar xvzf redis-stable.tar.gz`\
`cd redis-stable`\
`make`\
`make install`\
Запустить `redis` в консоли: `redis-server`, запустить `celery`: `celery worker -A tr_art --loglevel=debug --concurrency=4`, запустить службу `celery beat`: `celery -A tr_art beat`\
Поменять в `settings.py` почтовые настройки (`F7->smtp`)