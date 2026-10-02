import kronos
from django.conf import settings
from post_office.mail import send_queued_mail_until_done


#                 ┌───────────── Minute (0 - 59)
#                 │ ┌───────────── Hour (0 - 23)
#                 │ │ ┌───────────── Day of month (1 - 31)
#                 │ │ │ ┌───────────── Month (1 - 12)
#                 │ │ │ │ ┌───────────── Weekday (0 - 6)
#                 │ │ │ │ │
#                 * * * * *
@kronos.register("* * * * *")
def send_queued_mail():
    # building a custom lockfile_name so that multiple app on the same server can run this cron job
    lockfile_name = f"/tmp/{settings.BASE_DIR.name}_post_office.lock"
    send_queued_mail_until_done(lockfile_name)
