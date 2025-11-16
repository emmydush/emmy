from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, PurchaseItem
from products.models import Product
from suppliers.models import Supplier
from superadmin.middleware import get_current_business

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'expected_delivery_date', 'notes']
        widgets = {
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get current business from middleware
        current_business = get_current_business()
        if current_business:
            # Filter suppliers by current business
            self.fields['supplier'].queryset = Supplier.objects.filter(
                business=current_business, 
                is_active=True
            )
        else:
            # If no business context, show empty queryset
            self.fields['supplier'].queryset = Supplier.objects.none()

class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control unit-price-input', 'step': '0.01'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get current business from middleware
        current_business = get_current_business()
        if current_business:
            # Filter products by current business
            self.fields['product'].queryset = Product.objects.filter(
                business=current_business, 
                is_active=True
            )
        else:
            # If no business context, show empty queryset
            self.fields['product'].queryset = Product.objects.none()
            
        # Ensure the fields have the correct classes
        self.fields['product'].widget.attrs.update({'class': 'form-control product-select'})
        self.fields['quantity'].widget.attrs.update({'class': 'form-control'})
        self.fields['unit_price'].widget.attrs.update({'class': 'form-control unit-price-input'})

PurchaseItemFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseItem,
    form=PurchaseItemForm,
    extra=3,  # Show 3 empty forms by default
    can_delete=True
)