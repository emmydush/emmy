from products.models import Category
from superadmin.models import Business
from superadmin.middleware import set_current_business

# Try to get the business or create a test one
try:
    business = Business.objects.get(id=3)
except Business.DoesNotExist:
    # Create a test business if it doesn't exist
    user = None
    # Try to get any user
    from authentication.models import User
    if User.objects.exists():
        user = User.objects.first()
    else:
        # Create a test user if none exist
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    business = Business.objects.create(
        company_name='Test Business',
        owner=user,
        email='test@example.com',
        business_type='retail'
    )

print(f'Business: {business.id}')

# Set current business context
set_current_business(business)

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