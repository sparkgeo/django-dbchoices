Django DBChoices
================

Database driven choices for django model fields.


Quick start
-----------

1. Add "polls" to your INSTALLED_APPS setting like this::
```
    INSTALLED_APPS = [
        ...
        'dbchoices',
    ]
```
2. Run `python manage.py migrate` to create dbchoices models.
3. Start the development server and visit http://127.0.0.1:8000/admin/
to create choices and assign them to model fields.