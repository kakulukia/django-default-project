from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator, validate_email
from django.urls import reverse
from django.utils.safestring import mark_safe
from post_office import mail
from post_office.models import EmailTemplate


class Command(BaseCommand):
    help = "Queue an invitation to email signup with a passkey or password."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("--base-url", help="Application URL, including the local port if needed.")

    def handle(self, *args, **options):
        email = options["email"].strip()
        try:
            validate_email(email)
        except ValidationError as error:
            raise CommandError("Enter a valid email address.") from error
        site = Site.objects.get_current()
        scheme = "https" if settings.SECURE_SSL_REDIRECT else "http"
        base_url = options["base_url"] or f"{scheme}://{site.domain}"
        try:
            URLValidator(schemes=["http", "https"])(base_url)
            parsed = urlsplit(base_url)
        except (ValidationError, ValueError) as error:
            raise CommandError("Enter a valid HTTP(S) application URL.") from error
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise CommandError("Use an HTTP(S) application origin without credentials, path, query or fragment.")
        template, _ = EmailTemplate.objects.get_or_create(
            name="account_invitation",
            language="",
            default_template=None,
            defaults={
                "description": "Invitation to the public email-first signup flow.",
                "subject": "Einladung zu {{ site_name }}",
                "content": (
                    "Hallo,\n\n"
                    "du bist eingeladen, ein Konto bei {{ site_name }} anzulegen:\n\n"
                    "{{ signup_url }}\n\n"
                    "Bestätige dort deine E-Mail-Adresse mit dem zugesendeten Code "
                    "und richte anschließend einen Passkey oder ein Passwort ein.\n\n"
                    "Wenn du bereits ein Konto hast, kannst du dich hier anmelden:\n{{ login_url }}\n"
                ),
            },
        )
        base_url = base_url.rstrip("/")
        message = mail.send(
            email,
            template=template,
            context={
                "site_name": site.name,
                # The validated origin and encoded query are also used in plain text templates.
                "signup_url": mark_safe(
                    base_url + reverse("demo") + "?" + urlencode({"account": "signup", "email": email})
                ),
                "login_url": base_url + reverse("demo") + "?account=login",
            },
            priority="medium",
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Queued invitation #{message.pk}. Preview: /admin/post_office/email/{message.pk}/change/"
            )
        )
        self.stdout.write(message.message)
