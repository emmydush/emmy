from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, UserThemePreference

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "role", "password1", "password2")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone = self.cleaned_data["phone"]
        # Set role, default to 'cashier' if not provided
        user.role = self.cleaned_data.get("role", "cashier")
        if commit:
            user.save()
        return user


class AdminUserCreationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='cashier')
    
    def save(self, business):
        # Create user with provided details
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data.get('email', ''),
            password=self.cleaned_data['password']
        )
        
        # Set additional fields
        user.role = self.cleaned_data['role']
        user.first_name = ''
        user.last_name = ''
        user.phone = ''
        
        # Associate user with the business
        user.businesses.add(business)
        user.save()
        
        return user

class CustomAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        self.fields['remember_me'].widget.attrs.update({'class': 'form-check-input'})

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UserThemePreferenceForm(forms.ModelForm):
    class Meta:
        model = UserThemePreference
        fields = [
            'theme_mode',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'text_color',
            'sidebar_color',
            'card_color',
        ]
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'sidebar_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'card_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'theme_mode': forms.Select(attrs={'class': 'form-select'}),
        }