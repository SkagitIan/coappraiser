web: sh -c "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile - --capture-output"
