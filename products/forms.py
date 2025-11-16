from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category, Unit

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'barcode_format', 'category', 'unit', 'description',
            'image', 'cost_price', 'selling_price', 'quantity',
            'reorder_level', 'expiry_date', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'barcode': forms.TextInput(attrs={
                'placeholder': 'Leave blank to auto-generate barcode',
                'class': 'form-control'
            }),
            'barcode_format': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        # Extract the business from kwargs if provided
        self.business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        # Make barcode field not required since it will be auto-generated
        self.fields['barcode'].required = False
        # Add help text to explain barcode auto-generation
        self.fields['barcode'].help_text = 'Leave blank to automatically generate a barcode'
        self.fields['barcode_format'].help_text = 'Select the barcode format for scanning compatibility'
        
        # If we have a business context, filter categories and units by business
        if self.business:
            self.fields['category'].queryset = Category.objects.filter(business=self.business)
            self.fields['unit'].queryset = Unit.objects.filter(business=self.business)
        else:
            # If no business context, show empty querysets
            self.fields['category'].queryset = Category.objects.none()
            self.fields['unit'].queryset = Unit.objects.none()
        
    def clean_sku(self):
        sku = self.cleaned_data['sku']
        # If we have a business context, check for duplicate SKUs
        if self.business:
            # Exclude the current instance if we're updating
            queryset = Product.objects.filter(business=self.business, sku=sku)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
                
            if queryset.exists():
                raise ValidationError(f'A product with SKU "{sku}" already exists for your business. Please use a different SKU.')
        return sku

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'symbol']