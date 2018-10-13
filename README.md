Установка и запуск через docker:

Убедиться, что установлены docker и docker-compose\
Поменять абсолютные пути на свои в следующих местах:\
docker-compose.yml строка 8: у меня - /home/vadim/Documents/DJANGO_TRANSLATE/tr_art - папка с репой, т.е. .git расположен в ней\
docker-compose.yml строка 12\
docker-compose.yml строка 39\
/docker/nginx/default.conf строка 3 (art.sock в папке с settings.py)\
переименовать settings_docker.py в settings.py\
./manage.py collectstatic\
docker-compose up\

Предлагаю восстановить базу, в которой есть несколько категорий и языки https://www.dropbox.com/s/88rk7bjglc745sv/db.sql?dl=0 \
docker exec -ti art_psql1 $SHELL\
adduser vadim (имя пользователя можно изменить в settings.py и docker-compose.yml)\
sudo -i -u vadim\
cd / \
psql tr_art < db.sql (restore-им базу с категориями и языками)\

Если не хотим восстанавливать готовую базу, а хотим руками создать категории и языки с ./manage.py shell из контейнера:\
Зайти в контейнер web (docker exec -ti art_web1 $SHELL), выполнить ./app/tr_art/manage.py migrate\
Если не получается, закомментить в urls.py все, что связано со view - 1 импорт и сами урлы, убедиться, что прошла миграция для приложения articles\
Потом не забыть раскомментить\

Если ничего не получается, то можно запустить без докера:\
which python3\
virtualenv ./venv3 -p 'путь к питон3'\
source venv3/bin/activate\
pip install -r requirements.txt (лежит в docker/web)\
Переименовать settings_dev.py в settings.py\
Возможно, потребуется ./manage.py makemigrations ./manage.py migrate, возможно ./manage.py collectstatic\
./manage.py runserver 127.0.0.1:8003\
Пункт с restore-ом базы придется сделать, или создать языки и категории руками (самый быстрый вариант):\
./manage.py shell\
from articles.models import ArtCategory, ArtLanguage\
cats = ["Наука", "Юмор", "Политика", "История", "Фантастика"]\
langs = ["Русский", "Английский", "Татарский", "Иврит"]\
for c in cats:\
    ArtCategory.objects.create(name=c)\
for l in langs:\
    ArtLanguage.objects.create(name=l)\
