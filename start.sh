#!/bin/bash

# Ждём инициализации
sleep 2

# Запускаем gunicorn
echo "Starting gunicorn..."
exec gunicorn main:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
