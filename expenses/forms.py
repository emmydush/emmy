from django import forms
from .models import Expense, ExpenseCategory
from superadmin.middleware import get_current_business

class ExpenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the current business from middleware
        current_business = get_current_business()
        if current_business:
            # Filter categories by current business
            categories = ExpenseCategory.objects.filter(business=current_business)
            self.fields['category'].queryset = categories
            # If no categories exist, add a helpful message
            if not categories.exists():
                self.fields['category'].help_text = 'No categories available. Please create a category first.'
        else:
            # If no business context, show all categories (fallback)
            self.fields['category'].queryset = ExpenseCategory.objects.all()
            self.fields['category'].help_text = 'No business context found. Please select a business.'
    
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'date', 'description', 'receipt']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }