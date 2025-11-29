from django import forms
from .models import Sale, SaleItem, CreditSale, CreditPayment

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["customer", "payment_method", "discount", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "discount": forms.NumberInput(attrs={"step": "0.01"}),
        }


class CreditSaleForm(forms.ModelForm):
    class Meta:
        model = CreditSale
        fields = ["customer", "due_date", "notes"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class CreditPaymentForm(forms.ModelForm):
    class Meta:
        model = CreditPayment
        fields = ["amount", "payment_method", "notes"]
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }