from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Product,
    Category,
    Unit,
    StockAdjustment,
    ProductVariant,
    VariantAttribute,
    VariantAttributeValue,
    ProductVariantAttribute,
    InventoryTransfer,
)
from superadmin.models import Branch


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

        # If we have a business context, filter category and unit by business
        if self.business:
            self.fields["category"].queryset = Category.objects.filter(
                business=self.business
            )
            self.fields["unit"].queryset = Unit.objects.filter(business=self.business)

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

    def clean_barcode(self):
        barcode = self.cleaned_data.get("barcode")
        # If we have a business context and barcode is provided, check for duplicates
        if self.business and barcode:
            # Exclude the current instance if we're updating
            queryset = Product.objects.filter(business=self.business, barcode=barcode)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'A product with barcode "{barcode}" already exists for your business. Please use a different barcode.'
                )
        return barcode


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        # If we have a business context, check for duplicate category names
        if self.business:
            # Exclude the current instance if we're updating
            queryset = Category.objects.filter(business=self.business, name=name)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'A category with name "{name}" already exists for your business. Please use a different name.'
                )
        return name


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ["name", "symbol"]
        # Removed description field since it doesn't exist in the model

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        symbol = cleaned_data.get("symbol")

        # If we have a business context, check for duplicate unit names and symbols
        if self.business:
            # Check for duplicate name
            if name:
                name_queryset = Unit.objects.filter(business=self.business, name=name)
                if self.instance and self.instance.pk:
                    name_queryset = name_queryset.exclude(pk=self.instance.pk)

                if name_queryset.exists():
                    raise ValidationError(
                        f'A unit with name "{name}" already exists for your business. Please use a different name.'
                    )

            # Check for duplicate symbol
            if symbol:
                symbol_queryset = Unit.objects.filter(
                    business=self.business, symbol=symbol
                )
                if self.instance and self.instance.pk:
                    symbol_queryset = symbol_queryset.exclude(pk=self.instance.pk)

                if symbol_queryset.exists():
                    raise ValidationError(
                        f'A unit with symbol "{symbol}" already exists for your business. Please use a different symbol.'
                    )

        return cleaned_data


class StockAdjustmentForm(forms.ModelForm):
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

        # If we have a business context, filter products by business
        if self.business:
            self.fields["product"].queryset = Product.objects.filter(
                business=self.business
            )
        else:
            # If no business context, show empty queryset
            self.fields["product"].queryset = Product.objects.none()


class StockAdjustmentApprovalForm(forms.ModelForm):
    """Form for approving or rejecting stock adjustments"""

    class Meta:
        model = StockAdjustment
        fields = ["status", "approval_notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "approval_notes": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
        }


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
                    f'A variant with SKU "{sku}" already exists for your business. Please use a different SKU.'
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
        # If we have a business context, check for duplicate attribute names
        if self.business:
            # Exclude the current instance if we're updating
            queryset = VariantAttribute.objects.filter(
                business=self.business, name=name
            )
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
            queryset = VariantAttributeValue.objects.filter(
                business=self.business, attribute=attribute, value=value
            )
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'The value "{value}" already exists for attribute "{attribute.name}". Please use a different value.'
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
            self.fields["attribute_value"].queryset = (
                VariantAttributeValue.objects.filter(business=self.business)
            )
        else:
            # If no business context, show empty querysets
            self.fields["product_variant"].queryset = ProductVariant.objects.none()
            self.fields["attribute_value"].queryset = (
                VariantAttributeValue.objects.none()
            )


class InventoryTransferForm(forms.ModelForm):
    """Form for creating inventory transfers between branches"""

    class Meta:
        model = InventoryTransfer
        fields = [
            "from_branch",
            "to_branch",
            "product",
            "product_variant",
            "quantity",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "quantity": forms.NumberInput(attrs={"step": "0.01"}),
        }
        help_texts = {
            "quantity": "Enter the quantity to transfer",
        }

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # If we have a business context, filter branches, products and variants by business
        if self.business:
            self.fields["from_branch"].queryset = Branch.objects.filter(
                business=self.business, is_active=True
            )
            self.fields["to_branch"].queryset = Branch.objects.filter(
                business=self.business, is_active=True
            )
            self.fields["product"].queryset = Product.objects.filter(
                business=self.business, is_active=True
            )
            self.fields["product_variant"].queryset = ProductVariant.objects.filter(
                business=self.business, is_active=True
            )
        else:
            # If no business context, show empty querysets
            self.fields["from_branch"].queryset = Branch.objects.none()
            self.fields["to_branch"].queryset = Branch.objects.none()
            self.fields["product"].queryset = Product.objects.none()
            self.fields["product_variant"].queryset = ProductVariant.objects.none()

        # Exclude the "from_branch" field from "to_branch" queryset to prevent self-transfers
        if "from_branch" in self.data:
            try:
                from_branch_id = int(self.data.get("from_branch"))
                self.fields["to_branch"].queryset = self.fields[
                    "to_branch"
                ].queryset.exclude(id=from_branch_id)
            except (ValueError, TypeError):
                pass  # Invalid input from the client; ignore and fallback to default queryset
        elif self.instance.pk:
            self.fields["to_branch"].queryset = self.fields[
                "to_branch"
            ].queryset.exclude(pk=self.instance.from_branch.pk)

    def clean(self):
        cleaned_data = super().clean()
        from_branch = cleaned_data.get("from_branch")
        to_branch = cleaned_data.get("to_branch")
        product = cleaned_data.get("product")
        product_variant = cleaned_data.get("product_variant")
        quantity = cleaned_data.get("quantity")

        # Validate that from_branch and to_branch are different
        if from_branch and to_branch and from_branch == to_branch:
            raise ValidationError("Source and destination branches must be different.")

        # Validate that either product or product_variant is selected, but not both
        if not product and not product_variant:
            raise ValidationError(
                "Either a product or product variant must be selected."
            )
        if product and product_variant:
            raise ValidationError(
                "Only one of product or product variant can be selected."
            )

        # Validate quantity
        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        # Check available stock for the selected product/variant
        if product and from_branch:
            if product.branch == from_branch and product.quantity < quantity:
                raise ValidationError(
                    f"Insufficient stock in {from_branch.name}. Available: {product.quantity}, Requested: {quantity}"
                )
        elif product_variant and from_branch:
            if (
                product_variant.branch == from_branch
                and product_variant.quantity < quantity
            ):
                raise ValidationError(
                    f"Insufficient stock in {from_branch.name}. Available: {product_variant.quantity}, Requested: {quantity}"
                )

        return cleaned_data
