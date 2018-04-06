"""
WSGI config for this project.
It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""
import os

from dj_static import Cling, MediaCling
from django.core.wsgi import get_wsgi_application
from huepy import green, red

# async mail with uwsgi

try:
    # this will not work in the local dev server :(
    import uwsgidecorators
    from django.core.management import call_command

    @uwsgidecorators.timer(10)
    def send_queued_mail(num):
        """Send queued mail every 10 seconds"""
        call_command('send_queued_mail', processes=1)

    print(green('background mail queue activated'))

except ImportError:
    print(red("uwsgidecorators not found - background mails are unavailable!"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = MediaCling(Cling(get_wsgi_application()))
