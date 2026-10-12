from django.core.management.base import BaseCommand, CommandError
from post_office.models import Email


class Command(BaseCommand):
    help = "Print a queued or sent email without dispatching it."

    def add_arguments(self, parser):
        parser.add_argument("email_id", type=int)

    def handle(self, *args, **options):
        try:
            email = Email.objects.get(pk=options["email_id"])
        except Email.DoesNotExist as error:
            raise CommandError("Email not found.") from error
        message = email.email_message()
        self.stdout.write(f"To: {', '.join(message.to)}\nSubject: {message.subject}\n\n{message.body}")
