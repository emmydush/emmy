from django.core.management.base import BaseCommand
from authentication.models import User
from superadmin.models import Business
from settings.models import BusinessSettings


class Command(BaseCommand):
    help = "Check and fix business settings issues"

    def add_arguments(self, parser):
        parser.add_argument("--fix", action="store_true", help="Fix any issues found")
        parser.add_argument(
            "--business-id", type=int, help="Specific business ID to check"
        )

    def handle(self, *args, **options):
        fix_issues = options["fix"]
        business_id = options["business_id"]

        if business_id:
            businesses = Business.objects.filter(id=business_id)
            if not businesses.exists():
                self.stdout.write(
                    self.style.ERROR(f"Business with ID {business_id} not found")
                )
                return
        else:
            businesses = Business.objects.all()

        self.stdout.write(f"Checking {businesses.count()} businesses...")

        for business in businesses:
            self.stdout.write(
                f"\nChecking business: {business.company_name} (ID: {business.id})"
            )

            # Check if business has settings
            try:
                business_settings = BusinessSettings.objects.get(business=business)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Business settings found (ID: {business_settings.id})"
                    )
                )
            except BusinessSettings.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Business settings not found")
                )
                if fix_issues:
                    business_settings = BusinessSettings.objects.create(
                        business=business
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Created business settings (ID: {business_settings.id})"
                        )
                    )

            # Check if owner exists
            if business.owner:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Business owner: {business.owner.username}")
                )

                # Check if owner has settings access
                try:
                    from authentication.models import UserPermission

                    user_permission = UserPermission.objects.get(user=business.owner)
                    if user_permission.can_access_settings:
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ Owner has settings access")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ Owner does not have settings access"
                            )
                        )
                        if fix_issues:
                            user_permission.can_access_settings = True
                            user_permission.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ Granted settings access to owner"
                                )
                            )
                except UserPermission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Owner has no UserPermission record")
                    )
                    if fix_issues:
                        from authentication.models import UserPermission

                        user_permission = UserPermission.objects.create(
                            user=business.owner, can_access_settings=True
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Created UserPermission with settings access"
                            )
                        )
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠ Business has no owner"))

        self.stdout.write(self.style.SUCCESS("\nBusiness settings check completed"))
