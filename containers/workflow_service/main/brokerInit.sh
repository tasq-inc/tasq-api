#!/bin/sh

docker-entrypoint.sh rabbitmq-server &
sleep 30
python broker.py &
flower --port=5555 &
/usr/local/bin/celery -A worker worker --loglevel=info
