FROM python:3.4-stretch

RUN apt-get update && apt-get install -y mc

RUN mkdir -p /app/
WORKDIR /app/tr_art
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
