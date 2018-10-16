#!/bin/sh

psql -U postgres -c "CREATE USER $PG_USR PASSWORD '$PG_PWD'"
psql -U postgres -c "CREATE DATABASE $PG_DB OWNER $PG_USR"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $PG_DB TO $PG_USR"
