from django.core.management.base import BaseCommand
from authentication.models import User


class Command(BaseCommand):
    help = "Update user role"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username of the user to update")
        parser.add_argument("role", type=str, help="New role for the user")

    def handle(self, *args, **options):
        username = options["username"]
        role = options["role"]

        try:
            user = User.objects.get(username=username)
            user.role = role
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated {username} role to {role}")
            )
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} does not exist"))
