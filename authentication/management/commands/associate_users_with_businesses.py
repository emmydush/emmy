from django.core.management.base import BaseCommand
from authentication.models import User
from superadmin.models import Business


class Command(BaseCommand):
    help = "Associate existing users with businesses based on ownership"

    def handle(self, *args, **options):
        # Associate business owners with their businesses
        businesses = Business.objects.all()
        for business in businesses:
            # Associate the owner with the business
            business.owner.businesses.add(business)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Associated owner {business.owner.username} with business {business.company_name}"
                )
            )

        # For other users, we'll need to determine which business they should be associated with
        # This is a simplified approach - in a real application, you might have a more complex logic
        users = User.objects.filter(businesses__isnull=True)
        for user in users:
            # If the user is not an owner and not associated with any business,
            # we'll associate them with the first business they own (if any)
            owned_businesses = Business.objects.filter(owner=user)
            if owned_businesses.exists():
                business = owned_businesses.first()
                user.businesses.add(business)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Associated user {user.username} with business {business.company_name}"
                    )
                )
            else:
                # If the user doesn't own any business, we'll associate them with the first business
                # This is a fallback - in a real application, you might want to handle this differently
                first_business = Business.objects.first()
                if first_business:
                    user.businesses.add(first_business)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Associated user {user.username} with business {first_business.company_name} (fallback)"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS("Successfully associated all users with businesses")
        )
