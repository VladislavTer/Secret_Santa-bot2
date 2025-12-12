#!/bin/bash
echo "🚀 Запуск через gunicorn..."
gunicorn main:app \
  --bind 0.0.0.0:$PORT \
  --workers 1 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --preload
