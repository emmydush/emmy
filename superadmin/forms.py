from django import forms
from .models import Business, Branch, BranchRequest
from django.contrib.auth import get_user_model

User = get_user_model()


class BusinessRegistrationForm(forms.ModelForm):
    owner_email = forms.EmailField(
        label="Owner Email", help_text="Email of the business owner"
    )

    class Meta:
        model = Business
        fields = ["company_name", "email", "business_type"]
        labels = {
            "company_name": "Company Name",
            "email": "Business Email",
            "business_type": "Business Type",
        }
        help_texts = {
            "company_name": "Enter the official name of your company",
            "email": "Enter the main business email address",
            "business_type": "Select the type of business",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company_name"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["email"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["business_type"].widget.attrs.update({"class": "form-select bg-dark text-white"})
        self.fields["owner_email"].widget.attrs.update({"class": "form-control bg-dark text-white"})

    def clean_owner_email(self):
        owner_email = self.cleaned_data.get("owner_email")
        if User.objects.filter(email=owner_email).exists():
            raise forms.ValidationError(
                "A user with this email already exists. Please use a different email or log in."
            )
        return owner_email

    def save(self, commit=True):
        business = super().save(commit=False)
        # Set default values
        business.plan_type = "free"
        business.status = "pending"

        if commit:
            business.save()
        return business


class BusinessDetailsForm(forms.ModelForm):
    """Form for users to enter their business details after registration"""

    class Meta:
        model = Business
        fields = ["company_name", "email", "business_type"]
        labels = {
            "company_name": "Company Name",
            "email": "Business Email",
            "business_type": "Business Type",
        }
        help_texts = {
            "company_name": "Enter the official name of your company",
            "email": "Enter the main business email address",
            "business_type": "Select the type of business",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company_name"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["email"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["business_type"].widget.attrs.update({"class": "form-select bg-dark text-white"})


class BranchForm(forms.ModelForm):
    """Form for creating and updating branches"""

    class Meta:
        model = Branch
        fields = ["name", "address", "phone", "email", "is_main", "is_active"]
        labels = {
            "name": "Branch Name",
            "address": "Address",
            "phone": "Phone Number",
            "email": "Email Address",
            "is_main": "Main Branch",
            "is_active": "Active",
        }
        help_texts = {
            "name": "Enter the name of the branch",
            "address": "Enter the full address of the branch",
            "phone": "Enter the phone number for this branch",
            "email": "Enter the email address for this branch",
            "is_main": "Mark this as the main branch of your business",
            "is_active": "Uncheck to deactivate this branch",
        }

    def __init__(self, *args, **kwargs):
        # Extract the business from kwargs if provided
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["address"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["phone"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["email"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["is_main"].widget.attrs.update({"class": "form-check-input"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})

    def clean_name(self):
        name = self.cleaned_data["name"]
        # If we have a business context, check for duplicate branch names
        if self.business:
            # Exclude the current instance if we're updating
            queryset = Branch.objects.filter(business=self.business, name=name)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    f'A branch with name "{name}" already exists for your business. Please use a different name.'
                )
        return name

    def clean_is_main(self):
        is_main = self.cleaned_data["is_main"]
        # If this branch is being set as main, ensure no other branch is main
        if is_main and self.business:
            # Exclude the current instance if we're updating
            main_branches = Branch.objects.filter(business=self.business, is_main=True)
            if self.instance and self.instance.pk:
                main_branches = main_branches.exclude(pk=self.instance.pk)

            if main_branches.exists():
                raise forms.ValidationError(
                    "There is already a main branch for this business. Please unset it first or choose a different branch as main."
                )
        return is_main

    def save(self, commit=True):
        branch = super().save(commit=False)
        # Set the business if provided
        if self.business:
            branch.business = self.business

        if commit:
            branch.save()
        return branch


class BranchRequestForm(forms.ModelForm):
    """Form for business admins to request new branches"""
    
    class Meta:
        model = BranchRequest
        fields = ["name", "address", "phone", "email", "is_main"]
        labels = {
            "name": "Branch Name",
            "address": "Address",
            "phone": "Phone Number",
            "email": "Email Address",
            "is_main": "Main Branch",
        }
        help_texts = {
            "name": "Enter the name of the branch",
            "address": "Enter the full address of the branch",
            "phone": "Enter the phone number for this branch",
            "email": "Enter the email address for this branch",
            "is_main": "Mark this as the main branch of your business",
        }
    
    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["address"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["phone"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["email"].widget.attrs.update({"class": "form-control bg-dark text-white"})
        self.fields["is_main"].widget.attrs.update({"class": "form-check-input"})
    
    def clean_name(self):
        name = self.cleaned_data["name"]
        # If we have a business context, check for duplicate branch names
        if self.business:
            # Check if a branch with this name already exists
            if Branch.objects.filter(business=self.business, name=name).exists():
                raise forms.ValidationError(
                    f'A branch with name "{name}" already exists for your business. Please use a different name.'
                )
            # Also check if there's already a pending request with this name
            if BranchRequest.objects.filter(business=self.business, name=name, status="pending").exists():
                raise forms.ValidationError(
                    f'A request for a branch with name "{name}" is already pending approval. Please use a different name.'
                )
        return name
    
    def clean_is_main(self):
        is_main = self.cleaned_data["is_main"]
        # If this branch is being set as main, ensure no other branch is main
        if is_main and self.business:
            # Check existing branches
            if Branch.objects.filter(business=self.business, is_main=True).exists():
                raise forms.ValidationError(
                    "There is already a main branch for this business. Please unset it first or choose a different branch as main."
                )
            # Also check pending requests
            if BranchRequest.objects.filter(business=self.business, is_main=True, status="pending").exists():
                raise forms.ValidationError(
                    "There is already a request for a main branch pending approval. Please unset it first or choose a different branch as main."
                )
        return is_main
    
    def save(self, commit=True):
        branch_request = super().save(commit=False)
        # Set the business and requested_by if provided
        if self.business:
            branch_request.business = self.business
        
        if commit:
            branch_request.save()
        return branch_request


class BranchRequestApprovalForm(forms.ModelForm):
    """Form for superadmins to approve or reject branch requests"""
    
    class Meta:
        model = BranchRequest
        fields = ["status", "approval_notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control bg-dark text-white"}),
            "approval_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control bg-dark text-white"}),
        }