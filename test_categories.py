from products.models import Category
from superadmin.models import Business

# Get the business
business = Business.objects.get(id=3)
print(f'Business: {business.id}')

# Check if Electronics category exists
try:
    category = Category.objects.get(business=business, name='Electronics')
    print(f'Found existing category: {category.name}')
except Category.DoesNotExist:
    print('Category does not exist')
    # Try to create it
    try:
        category = Category.objects.create(
            business=business,
            name='Electronics',
            description='Test category'
        )
        print(f'Created category: {category.name}')
    except Exception as e:
        print(f'Error creating category: {e}')