from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, UserThemePreference, UserPermission


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "profile_picture",
            "password1",
            "password2",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone = self.cleaned_data["phone"]
        user.profile_picture = self.cleaned_data.get("profile_picture")
        # Set role, default to 'cashier' if not provided
        user.role = self.cleaned_data.get("role", "cashier")
        if commit:
            user.save()
        return user


class AdminUserCreationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial="cashier", widget=forms.Select(attrs={'class': 'form-select'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        # Validate the password using Django's password validation
        from django.contrib.auth.password_validation import validate_password
        try:
            validate_password(password)
        except forms.ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def save(self, business):
        # Create user with provided details
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data.get("email", ""),
            password=self.cleaned_data["password"],
        )

        # Set additional fields
        user.role = self.cleaned_data["role"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.phone = self.cleaned_data.get("phone", "")

        # Associate user with the business
        user.businesses.add(business)
        user.save()

        return user


class CustomAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password"].widget.attrs.update({"class": "form-control"})
        self.fields["remember_me"].widget.attrs.update({"class": "form-check-input"})


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "profile_picture",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "profile_picture": forms.FileInput(attrs={"class": "form-control"}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if this email is already used by another user
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email


class UserPermissionForm(forms.ModelForm):
    class Meta:
        model = UserPermission
        fields = [
            "can_access_products",
            "can_access_sales",
            "can_access_purchases",
            "can_access_customers",
            "can_access_suppliers",
            "can_access_expenses",
            "can_access_reports",
            "can_access_settings",
            "can_manage_users",
            "can_create_users",
            "can_edit_users",
            "can_delete_users",
            "can_create",
            "can_edit",
            "can_delete",
        ]
        widgets = {
            "can_access_products": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_access_sales": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_access_purchases": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_access_customers": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_access_suppliers": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_access_expenses": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_access_reports": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_access_settings": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_manage_users": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_create_users": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_edit_users": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_delete_users": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "can_create": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_edit": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "can_delete": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        # Add any cross-field validation if needed
        return cleaned_data


class UserThemePreferenceForm(forms.ModelForm):
    class Meta:
        model = UserThemePreference
        fields = [
            "theme_mode",
            "primary_color",
            "secondary_color",
            "accent_color",
            "background_color",
            "text_color",
            "sidebar_color",
            "card_color",
        ]
        widgets = {
            "primary_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "secondary_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "accent_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "background_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "text_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "sidebar_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "card_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "theme_mode": forms.Select(attrs={"class": "form-select"}),
        }
