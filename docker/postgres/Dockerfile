FROM postgres:10

RUN apt-get update && apt-get install sudo

COPY db_setup.sh /docker-entrypoint-initdb.d/01-db-setup.sh
