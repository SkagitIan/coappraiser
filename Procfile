web: sh -c "python manage.py migrate --noinput || echo migrate failed; exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
