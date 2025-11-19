from django import forms
from .models import Sale, SaleItem


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["customer", "payment_method", "discount", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "discount": forms.NumberInput(attrs={"step": "0.01"}),
        }
