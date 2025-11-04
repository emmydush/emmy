from django import forms
from .models import Business
from django.contrib.auth import get_user_model

User = get_user_model()

class BusinessRegistrationForm(forms.ModelForm):
    owner_email = forms.EmailField(
        label="Owner Email",
        help_text="Email of the business owner"
    )
    
    class Meta:
        model = Business
        fields = ['company_name', 'email', 'business_type']
        labels = {
            'company_name': 'Company Name',
            'email': 'Business Email',
            'business_type': 'Business Type',
        }
        help_texts = {
            'company_name': 'Enter the official name of your company',
            'email': 'Enter the main business email address',
            'business_type': 'Select the type of business',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['business_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['owner_email'].widget.attrs.update({'class': 'form-control'})

    def clean_owner_email(self):
        owner_email = self.cleaned_data.get('owner_email')
        if User.objects.filter(email=owner_email).exists():
            raise forms.ValidationError("A user with this email already exists. Please use a different email or log in.")
        return owner_email

    def save(self, commit=True):
        business = super().save(commit=False)
        # Set default values
        business.plan_type = 'free'
        business.status = 'pending'
        
        if commit:
            business.save()
        return business

class BusinessDetailsForm(forms.ModelForm):
    """Form for users to enter their business details after registration"""
    
    class Meta:
        model = Business
        fields = ['company_name', 'email', 'business_type']
        labels = {
            'company_name': 'Company Name',
            'email': 'Business Email',
            'business_type': 'Business Type',
        }
        help_texts = {
            'company_name': 'Enter the official name of your company',
            'email': 'Enter the main business email address',
            'business_type': 'Select the type of business',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['business_type'].widget.attrs.update({'class': 'form-select'})