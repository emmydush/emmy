from django import forms
from .models import Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "name",
            "email",
            "phone",
            "address",
            "company",
            "tax_id",
            "contact_person",
            "contact_person_phone",
            "contact_person_email",
            "is_active",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }
