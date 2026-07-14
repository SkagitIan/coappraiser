# Preflight operations

Run `python manage.py migrate`, `python manage.py check`, and `python manage.py test apps.preflight`. The initial implementation processes small packages synchronously. A future worker should make every stage idempotent using version, file hash, parser version, and rule version, and should stop safely when a review is deleted.
