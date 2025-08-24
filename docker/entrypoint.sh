#!/bin/sh
set -e

export DJANGO_SETTINGS_MODULE=django_project.settings

# マイグレーション（失敗時はコンテナ停止）
echo "Running migrations..."
python manage.py migrate --noinput

# 静的ファイル収集
echo "Collecting static files..."
python manage.py collectstatic --noinput

# アプリ起動
echo "Starting Gunicorn..."
exec gunicorn django_project.wsgi:application --bind 0.0.0.0:$PORT --workers 3
