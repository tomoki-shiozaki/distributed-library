set -e

export DJANGO_SETTINGS_MODULE=django_project.settings

# マイグレーション（失敗時はコンテナ停止）
echo "Running migrations..."
python manage.py migrate --noinput

# アプリ起動
echo "Starting Gunicorn..."
exec gunicorn django_project.wsgi:application --bind 0.0.0.0:$PORT --workers 3
