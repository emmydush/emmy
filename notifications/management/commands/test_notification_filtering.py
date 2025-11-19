from django.core.management.base import BaseCommand
from notifications.models import Notification
from authentication.models import User
from superadmin.models import Business


class Command(BaseCommand):
    help = "Test that users only see notifications for their own business"

    def handle(self, *args, **options):
        # Get all users with businesses
        users_with_businesses = User.objects.filter(
            owned_businesses__isnull=False
        ).distinct()

        self.stdout.write(
            f"Found {users_with_businesses.count()} users with businesses"
        )

        for user in users_with_businesses:
            user_businesses = user.owned_businesses.all()
            self.stdout.write(f"\nUser: {user.username}")
            self.stdout.write(
                f"Businesses: {[b.company_name for b in user_businesses]}"
            )

            # Get user's notifications
            user_notifications = Notification.objects.filter(recipient=user)
            self.stdout.write(f"Total notifications: {user_notifications.count()}")

            # Get user's business-specific notifications
            business_notifications = Notification.objects.filter(
                recipient=user, business__in=user_businesses
            )
            self.stdout.write(
                f"Business-specific notifications: {business_notifications.count()}"
            )

            # Check if all notifications belong to user's businesses
            all_correct = True
            for notification in user_notifications:
                if (
                    notification.business
                    and notification.business not in user_businesses
                ):
                    self.stdout.write(
                        self.style.ERROR(
                            f"ERROR: Notification {notification.id} belongs to business "
                            f"{notification.business.company_name} which is not owned by {user.username}"
                        )
                    )
                    all_correct = False

            if all_correct:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"All notifications for {user.username} are correctly filtered by business context"
                    )
                )
