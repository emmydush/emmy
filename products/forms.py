from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category, Unit, StockAdjustment, ProductVariant, VariantAttribute, VariantAttributeValue, ProductVariantAttribute

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "barcode",
            "barcode_format",
            "category",
            "unit",
            "description",
            "image",
            "cost_price",
            "selling_price",
            "quantity",
            "reorder_level",
            "expiry_date",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "barcode": forms.TextInput(
                attrs={
                    "placeholder": "Leave blank to auto-generate barcode",
                    "class": "form-control",
                }
            ),
            "barcode_format": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        # Extract the business from kwargs if provided
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)
        # Make barcode field not required since it will be auto-generated
        self.fields["barcode"].required = False
        # Add help text to explain barcode auto-generation
        self.fields["barcode"].help_text = (
            "Leave blank to automatically generate a barcode"
        )
        self.fields["barcode_format"].help_text = (
            "Select the barcode format for scanning compatibility"
        )

        # If we have a business context, filter categories and units by business
        if self.business:
            self.fields["category"].queryset = Category.objects.filter(
                business=self.business
            )
            self.fields["unit"].queryset = Unit.objects.filter(business=self.business)
        else:
            # If no business context, show empty querysets
            self.fields["category"].queryset = Category.objects.none()
            self.fields["unit"].queryset = Unit.objects.none()

    def clean_sku(self):
        sku = self.cleaned_data["sku"]
        # If we have a business context, check for duplicate SKUs
        if self.business:
            # Exclude the current instance if we're updating
            queryset = Product.objects.filter(business=self.business, sku=sku)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'A product with SKU "{sku}" already exists for your business. Please use a different SKU.'
                )
        return sku


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ["name", "symbol"]


class StockAdjustmentForm(forms.ModelForm):
    """Form for requesting stock adjustments"""

    class Meta:
        model = StockAdjustment
        fields = ["product", "adjustment_type", "quantity", "reason", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "quantity": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)

        # Filter products by business
        if self.business:
            self.fields["product"].queryset = Product.objects.filter(
                business=self.business
            )

        # Add CSS classes
        for field in self.fields:
            if not isinstance(self.fields[field], forms.BooleanField):
                self.fields[field].widget.attrs.update({"class": "form-control"})

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        adjustment_type = cleaned_data.get("adjustment_type")
        product = cleaned_data.get("product")
        quantity = cleaned_data.get("quantity")

        # For stock out requests, check if there's enough stock
        if adjustment_type == "out" and product and quantity:
            if quantity > product.quantity:
                raise forms.ValidationError(
                    f"Cannot remove {quantity} items. Only {product.quantity} available in stock."
                )

        return cleaned_data


class StockAdjustmentApprovalForm(forms.ModelForm):
    """Form for approving/rejecting stock adjustments"""

    class Meta:
        model = StockAdjustment
        fields = ["status", "approval_notes"]
        widgets = {
            "approval_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields:
            if not isinstance(self.fields[field], forms.BooleanField):
                self.fields[field].widget.attrs.update({"class": "form-control"})


class ProductVariantForm(forms.ModelForm):
    """Form for creating and updating product variants"""
    
    class Meta:
        model = ProductVariant
        fields = [
            "name",
            "sku",
            "barcode",
            "barcode_format",
            "cost_price",
            "selling_price",
            "quantity",
            "reorder_level",
            "image",
            "is_active",
        ]
        widgets = {
            "barcode": forms.TextInput(
                attrs={
                    "placeholder": "Leave blank to auto-generate barcode",
                    "class": "form-control",
                }
            ),
            "barcode_format": forms.Select(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        # Extract the business and product from kwargs if provided
        self.business = kwargs.pop("business", None)
        self.product = kwargs.pop("product", None)
        super().__init__(*args, **kwargs)
        # Make barcode field not required since it will be auto-generated
        self.fields["barcode"].required = False
        # Add help text to explain barcode auto-generation
        self.fields["barcode"].help_text = (
            "Leave blank to automatically generate a barcode"
        )
        self.fields["barcode_format"].help_text = (
            "Select the barcode format for scanning compatibility"
        )

    def clean_sku(self):
        sku = self.cleaned_data["sku"]
        # If we have a business context, check for duplicate SKUs
        if self.business:
            # Exclude the current instance if we're updating
            queryset = ProductVariant.objects.filter(business=self.business, sku=sku)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'A product variant with SKU "{sku}" already exists for your business. Please use a different SKU.'
                )
        return sku


class VariantAttributeForm(forms.ModelForm):
    """Form for creating and updating variant attributes"""
    
    class Meta:
        model = VariantAttribute
        fields = ["name", "description", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        # If we have a business context, check for duplicate names
        if self.business:
            # Exclude the current instance if we're updating
            queryset = VariantAttribute.objects.filter(business=self.business, name=name)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'A variant attribute with name "{name}" already exists for your business. Please use a different name.'
                )
        return name


class VariantAttributeValueForm(forms.ModelForm):
    """Form for creating and updating variant attribute values"""
    
    class Meta:
        model = VariantAttributeValue
        fields = ["attribute", "value", "description", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)
        
        # If we have a business context, filter attributes by business
        if self.business:
            self.fields["attribute"].queryset = VariantAttribute.objects.filter(
                business=self.business
            )
        else:
            # If no business context, show empty queryset
            self.fields["attribute"].queryset = VariantAttribute.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        attribute = cleaned_data.get("attribute")
        value = cleaned_data.get("value")
        
        # If we have a business context, check for duplicate attribute-value combinations
        if self.business and attribute and value:
            # Exclude the current instance if we're updating
            queryset = VariantAttributeValue.objects.filter(
                business=self.business, attribute=attribute, value=value
            )
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'The value "{value}" already exists for attribute "{attribute.name}" in your business. Please use a different value.'
                )
        return cleaned_data


class ProductVariantAttributeForm(forms.ModelForm):
    """Form for linking product variants to their attribute values"""
    
    class Meta:
        model = ProductVariantAttribute
        fields = ["product_variant", "attribute_value"]
        
    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        self.product_variant = kwargs.pop("product_variant", None)
        super().__init__(*args, **kwargs)
        
        # If we have a business context, filter variants and attribute values by business
        if self.business:
            self.fields["product_variant"].queryset = ProductVariant.objects.filter(
                business=self.business
            )
            self.fields["attribute_value"].queryset = VariantAttributeValue.objects.filter(
                business=self.business
            )
        else:
            # If no business context, show empty querysets
            self.fields["product_variant"].queryset = ProductVariant.objects.none()
            self.fields["attribute_value"].queryset = VariantAttributeValue.objects.none()
