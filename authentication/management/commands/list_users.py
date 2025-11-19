from django.core.management.base import BaseCommand
from authentication.models import User


class Command(BaseCommand):
    help = "List all users and their roles"

    def handle(self, *args, **options):
        users = User.objects.all()

        if not users:
            self.stdout.write("No users found")
            return

        self.stdout.write("Users and their roles:")
        self.stdout.write("=" * 40)

        for user in users:
            self.stdout.write(f"{user.username:<20} | {user.role:<15} | {user.email}")

        self.stdout.write("=" * 40)
        self.stdout.write(f"Total users: {len(users)}")
