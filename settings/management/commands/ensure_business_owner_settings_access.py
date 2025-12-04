from django.core.management.base import BaseCommand
from authentication.models import User, UserPermission
from superadmin.models import Business


class Command(BaseCommand):
    help = (
        "Ensure all business owners have proper permissions to access business settings"
    )

    def handle(self, *args, **options):
        # Get all businesses that have an owner
        businesses_with_owner = Business.objects.exclude(owner=None)

        self.stdout.write(
            f"Found {businesses_with_owner.count()} businesses with owners"
        )

        updated_count = 0

        for business in businesses_with_owner:
            owner = business.owner

            # Get or create UserPermission for the owner
            user_permission, created = UserPermission.objects.get_or_create(user=owner)

            # Check if the owner already has settings access
            if not user_permission.can_access_settings:
                user_permission.can_access_settings = True
                user_permission.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Granted settings access to {owner.username} (owner of {business.company_name})"
                    )
                )
                updated_count += 1
            else:
                self.stdout.write(
                    f"{owner.username} (owner of {business.company_name}) already has settings access"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated permissions for {updated_count} business owners"
            )
        )
