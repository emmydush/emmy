from django.core.management.base import BaseCommand
from notifications.models import Notification
from superadmin.models import Business


class Command(BaseCommand):
    help = "Clean up notifications to ensure users only see notifications for their own business"

    def handle(self, *args, **options):
        # Get all notifications
        all_notifications = Notification.objects.all()
        self.stdout.write(f"Total notifications: {all_notifications.count()}")

        # Count and fix mismatched notifications
        mismatched_count = 0
        fixed_count = 0

        for notification in all_notifications:
            # Check if notification has a business but recipient doesn't own that business
            if notification.business:
                # Check if recipient owns this business
                if not notification.recipient.owned_businesses.filter(
                    id=notification.business.id
                ).exists():
                    mismatched_count += 1
                    # For now, we'll just delete these mismatched notifications
                    # In a real system, you might want to reassign them or handle differently
                    notification.delete()
                    fixed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {mismatched_count} mismatched notifications, fixed {fixed_count}"
            )
        )

        # Now verify all remaining notifications are correct
        remaining_notifications = Notification.objects.all()
        still_mismatched = 0

        for notification in remaining_notifications:
            if notification.business:
                # Check if recipient owns this business
                if not notification.recipient.owned_businesses.filter(
                    id=notification.business.id
                ).exists():
                    still_mismatched += 1

        if still_mismatched == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "All notifications are now correctly filtered by business context"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"There are still {still_mismatched} mismatched notifications"
                )
            )
