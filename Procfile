web: sh -c "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - --capture-output"
