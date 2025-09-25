FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# data dir for sqlite + CA keys
RUN mkdir -p /data
VOLUME ["/data"]

ENV PYTHONUNBUFFERED=1
EXPOSE 5000
