from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from authentication.models import User
import getpass

class Command(BaseCommand):
    help = 'Reset the password for the superadmin user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username of the superadmin user to reset')
        parser.add_argument('--password', type=str, help='New password (if not provided, will prompt)')
        parser.add_argument('--noinput', action='store_true', help='Do not prompt for confirmation')

    def handle(self, *args, **options):
        username = options.get('username') or 'admin'
        
        try:
            user = User.objects.get(username=username, is_superuser=True)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Superadmin user "{username}" does not exist')
            )
            return

        # Get password
        if options.get('password'):
            password = options['password']
        else:
            password = getpass.getpass('Enter new password: ')
            confirm_password = getpass.getpass('Confirm new password: ')
            
            if password != confirm_password:
                self.stdout.write(
                    self.style.ERROR('Passwords do not match')
                )
                return

        # Confirm if not using --noinput
        if not options.get('noinput'):
            confirm = input(f'Are you sure you want to reset the password for user "{username}"? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(
                    self.style.WARNING('Password reset cancelled')
                )
                return

        # Reset password
        user.set_password(password)
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully reset password for superadmin user "{username}"')
        )