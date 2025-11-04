from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from superadmin.models import Business

User = get_user_model()

@receiver(post_save, sender=Business)
def associate_owner_with_business(sender, instance, created, **kwargs):
    """
    Signal to automatically associate the business owner with the business
    when a new business is created.
    """
    if created:
        # The owner is already associated through the ForeignKey relationship
        # But we can add additional logic here if needed
        pass