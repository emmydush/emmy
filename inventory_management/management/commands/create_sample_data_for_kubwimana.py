from django.core.management.base import BaseCommand
from sales.models import Sale, SaleItem
from products.models import Product, Category, Unit
from customers.models import Customer
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random
from superadmin.models import Business
from authentication.models import User

class Command(BaseCommand):
    help = 'Create sample data for kubwimana user: 150 products, 50 customers, 10 sales'

    def handle(self, *args, **options):
        # Get the user by username
        try:
            user = User.objects.get(username='kubwimana')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User kubwimana does not exist'))
            return
            
        # Get the user's business
        try:
            business = Business.objects.get(owner=user)
        except Business.DoesNotExist:
            self.stdout.write(self.style.ERROR('No business found for user kubwimana'))
            return
            
        self.stdout.write(f'Creating data for user {user.username} with business {business.company_name}')
        
        # First, ensure we have categories and units for this business
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and accessories'},
            {'name': 'Clothing', 'description': 'Apparel and fashion items'},
            {'name': 'Food & Beverages', 'description': 'Food products and drinks'},
            {'name': 'Home & Garden', 'description': 'Home improvement and garden supplies'},
            {'name': 'Sports & Outdoors', 'description': 'Sports equipment and outdoor gear'},
            {'name': 'Beauty & Personal Care', 'description': 'Cosmetics and personal care items'},
            {'name': 'Toys & Games', 'description': 'Toys for children and games'},
            {'name': 'Automotive', 'description': 'Car accessories and automotive supplies'},
            {'name': 'Health & Wellness', 'description': 'Health products and wellness items'},
            {'name': 'Office Supplies', 'description': 'Office and stationery supplies'},
        ]
        
        units_data = [
            {'name': 'Piece', 'symbol': 'pc'},
            {'name': 'Kilogram', 'symbol': 'kg'},
            {'name': 'Liter', 'symbol': 'L'},
            {'name': 'Box', 'symbol': 'box'},
            {'name': 'Dozen', 'symbol': 'dz'},
            {'name': 'Pair', 'symbol': 'pr'},
            {'name': 'Meter', 'symbol': 'm'},
            {'name': 'Milliliter', 'symbol': 'ml'},
        ]
        
        # Create categories for this business
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                business=business,
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            
        # Create units for this business
        units = []
        for unit_data in units_data:
            unit, created = Unit.objects.get_or_create(
                business=business,
                name=unit_data['name'],
                defaults={'symbol': unit_data['symbol']}
            )
            units.append(unit)
        
        # Create 150 products for this business
        product_names = [
            'Smartphone', 'Laptop', 'Tablet', 'Smart Watch', 'Bluetooth Speaker',
            'Wireless Headphones', 'Gaming Console', 'Digital Camera', 'Fitness Tracker', 'Smart TV',
            'Printer', 'Scanner', 'External Hard Drive', 'USB Flash Drive', 'Router',
            'T-Shirt', 'Jeans', 'Dress', 'Jacket', 'Sweater',
            'Shorts', 'Skirt', 'Blouse', 'Socks', 'Underwear',
            'Sneakers', 'Sandals', 'Boots', 'Slippers', 'Formal Shoes',
            'Coffee', 'Tea', 'Juice', 'Soda', 'Energy Drink',
            'Water', 'Milk', 'Yogurt', 'Cheese', 'Bread',
            'Rice', 'Pasta', 'Cereal', 'Chips', 'Chocolate',
            'Garden Tools Set', 'Lawn Mower', 'Hose', 'Sprinkler', 'Fertilizer',
            'Plant Seeds', 'Potting Soil', 'Garden Gloves', 'Pruning Shears', 'Wheelbarrow',
            'Basketball', 'Soccer Ball', 'Tennis Racket', 'Baseball Glove', 'Golf Clubs',
            'Swimming Goggles', 'Treadmill', 'Yoga Mat', 'Dumbbells', 'Exercise Bike',
            'Sunscreen', 'Shampoo', 'Conditioner', 'Body Lotion', 'Face Cream',
            'Makeup Kit', 'Perfume', 'Nail Polish', 'Hair Dryer', 'Electric Razor',
            'Board Game', 'Puzzle', 'Action Figure', 'Doll', 'Toy Car',
            'Building Blocks', 'Stuffed Animal', 'Musical Instrument', 'Art Supplies', 'Educational Toy',
            'Car Charger', 'Phone Mount', 'Tire Pressure Gauge', 'Car Wax', 'Air Freshener',
            'Motor Oil', 'Car Battery', 'Windshield Wipers', 'Car Cover', 'Seat Covers',
            'Vitamins', 'Protein Powder', 'Multivitamin', 'Face Mask', 'Hand Sanitizer',
            'Notebook', 'Pen Set', 'Stapler', 'Paper Clips', 'Binder',
            'Desk Lamp', 'Office Chair', 'File Cabinet', 'Whiteboard', 'Calculator',
            'Coffee Maker', 'Blender', 'Toaster', 'Microwave', 'Refrigerator',
            'Washing Machine', 'Dryer', 'Vacuum Cleaner', 'Iron', 'Hair Straightener',
            'Electric Kettle', 'Food Processor', 'Rice Cooker', 'Air Fryer', 'Slow Cooker',
            'Bluetooth Earbuds', 'Smart Speaker', 'Tablet Stand', 'Phone Case', 'Screen Protector',
            'Wireless Charger', 'Power Bank', 'USB Cable', 'HDMI Cable', 'Ethernet Cable',
            'Webcam', 'Microphone', 'Headset', 'Speakers', 'Soundbar',
            'Graphics Card', 'RAM Memory', 'SSD Drive', 'Motherboard', 'CPU Processor',
            'Mechanical Keyboard', 'Gaming Mouse', 'Monitor', 'Printer Ink', 'Toner Cartridge',
            'Business Cards', 'Letterhead', 'Envelopes', 'Stamps', 'Post-it Notes',
            'Highlighters', 'Markers', 'Colored Pencils', 'Sketchbook', 'Paint Set',
            'Fitness Tracker', 'Smart Scale', 'Blood Pressure Monitor', 'Pedometer', 'Sleep Tracker',
            'Resistance Bands', 'Jump Rope', 'Foam Roller', 'Massage Gun', 'Compression Socks',
            'Skincare Set', 'Face Mask', 'Serum', 'Moisturizer', 'Cleanser',
            'Sun Hat', 'Sunglasses', 'Beach Towel', 'Cooler', 'Camping Chair',
            'Hiking Boots', 'Backpack', 'Sleeping Bag', 'Tent', 'Flashlight',
            'Protein Bars', 'Sports Drink', 'Energy Gel', 'Electrolyte Tablets', 'Recovery Shake',
            'Running Shoes', 'Cycling Helmet', 'Swimsuit', 'Gym Bag', 'Water Bottle',
            'Smart Thermostat', 'Security Camera', 'Doorbell', 'Smart Lock', 'Light Bulbs',
            'Extension Cord', 'Power Strip', 'Surge Protector', 'Battery Pack', 'Flashlight',
            'Toolbox', 'Screwdriver Set', 'Hammer', 'Wrench Set', 'Pliers',
            'Drill', 'Saw', 'Measuring Tape', 'Level', 'Stud Finder',
            'Paint Brush', 'Roller', 'Drop Cloth', 'Painter\'s Tape', 'Sandpaper',
            'Shovel', 'Rake', 'Hoe', 'Garden Fork', 'Pruning Saw',
            'Bird Feeder', 'Bird Bath', 'Garden Statue', 'Wind Chime', 'Solar Light',
            'Pet Food', 'Pet Toy', 'Pet Bed', 'Pet Carrier', 'Pet Grooming Kit',
            'Baby Diapers', 'Baby Wipes', 'Baby Food', 'Baby Clothes', 'Baby Toys',
            'Book', 'Magazine', 'Newspaper', 'E-reader', 'Audiobook',
            'DVD', 'Blu-ray', 'Video Game', 'Gaming Accessories', 'Console Controller',
            'Camera Lens', 'Tripod', 'Camera Bag', 'Memory Card', 'Camera Battery',
            'Drone', 'RC Car', 'Model Kit', 'Collectible Figure', 'Trading Cards',
            'Musical Instrument', 'Sheet Music', 'Music Stand', 'Tuner', 'Metronome',
            'Art Canvas', 'Paint Brushes', 'Acrylic Paint', 'Watercolor Set', 'Drawing Pencils',
            'Sewing Machine', 'Fabric', 'Thread', 'Buttons', 'Zipper',
            'Leather Wallet', 'Sunglasses Case', 'Travel Adapter', 'Luggage', 'Suitcase',
            'Backpack', 'Messenger Bag', 'Laptop Bag', 'Briefcase', 'Handbag',
            'Watch', 'Jewelry', 'Necklace', 'Bracelet', 'Earrings',
            'Wallet', 'Keychain', 'Phone Wallet', 'Lanyard', 'Business Card Holder',
            'Coffee Beans', 'Tea Bags', 'Spices', 'Herbs', 'Condiments',
            'Canned Goods', 'Frozen Food', 'Snack Mix', 'Granola Bars', 'Dried Fruit',
            'Baby Formula', 'Pet Food', 'Cat Litter', 'Dog Treats', 'Fish Food',
            'Plant Fertilizer', 'Pesticide', 'Weed Killer', 'Insect Repellent', 'Rodent Bait',
            'Car Wax', 'Tire Shine', 'Dashboard Cleaner', 'Glass Cleaner', 'Carpet Cleaner',
            'Laundry Detergent', 'Fabric Softener', 'Stain Remover', 'Bleach', 'Disinfectant',
            'Toothpaste', 'Toothbrush', 'Mouthwash', 'Dental Floss', 'Electric Toothbrush',
            'Shaving Cream', 'Razor Blades', 'Aftershave', 'Deodorant', 'Antiperspirant',
            'Face Wash', 'Toner', 'Serum', 'Moisturizer', 'Night Cream',
            'Sunscreen', 'Lip Balm', 'Makeup Remover', 'Cotton Pads', 'Facial Mask',
            'Hair Shampoo', 'Hair Conditioner', 'Hair Mask', 'Hair Oil', 'Hair Spray',
            'Nail Clippers', 'Nail File', 'Cuticle Oil', 'Hand Cream', 'Foot Cream',
            'Vitamins', 'Supplements', 'Protein Powder', 'Meal Replacement', 'Energy Boost',
            'Cold Medicine', 'Allergy Relief', 'Pain Relievers', 'First Aid', 'Bandages',
            'Thermometer', 'Blood Pressure Monitor', 'Glucose Meter', 'Pulse Oximeter', 'Scale',
            'Fitness Equipment', 'Exercise Mat', 'Resistance Bands', 'Dumbbells', 'Kettlebell',
            'Yoga Block', 'Foam Roller', 'Massage Ball', 'Compression Gear', 'Workout Gloves',
            'Running Shorts', 'Sports Bra', 'Compression Socks', 'Athletic Tape', 'Sports Towel',
            'Swimming Goggles', 'Swim Cap', 'Swim Fins', 'Kickboard', 'Pull Buoy',
            'Tennis Balls', 'Golf Balls', 'Baseballs', 'Softballs', 'Basketballs',
            'Soccer Balls', 'Volleyballs', 'Footballs', 'Hockey Puck', 'Skateboard',
            'Bicycle', 'Helmet', 'Bike Lock', 'Bike Pump', 'Bike Lights',
            'Camping Tent', 'Sleeping Bag', 'Camping Stove', 'Cooler', 'Lantern',
            'Hiking Boots', 'Backpack', 'Trail Mix', 'Water Purifier', 'Compass',
            'Smartphone Case', 'Screen Protector', 'Pop Socket', 'Car Mount', 'Wireless Charger',
            'Laptop Sleeve', 'Tablet Case', 'Keyboard Cover', 'Mouse Pad', 'Laptop Stand',
            'USB Hub', 'External SSD', 'Memory Card Reader', 'Charging Cable', 'Power Adapter',
            'Bluetooth Speaker', 'Headphones', 'Earbuds', 'Microphone', 'Webcam',
            'Gaming Chair', 'Desk', 'Monitor Stand', 'Cable Management', 'LED Strip',
            'Coffee Table', 'Sofa', 'Armchair', 'Bookshelf', 'TV Stand',
            'Dining Table', 'Dining Chairs', 'Bar Stool', 'Kitchen Island', 'Pantry',
            'Bed Frame', 'Mattress', 'Pillow', 'Bed Sheets', 'Comforter',
            'Dresser', 'Nightstand', 'Wardrobe', 'Closet Organizer', 'Laundry Basket',
            'Refrigerator', 'Oven', 'Microwave', 'Dishwasher', 'Washing Machine',
            'Dryer', 'Vacuum Cleaner', 'Iron', 'Steamer', 'Air Purifier',
            'Blender', 'Food Processor', 'Toaster', 'Coffee Maker', 'Kettle',
            'Rice Cooker', 'Slow Cooker', 'Pressure Cooker', 'Air Fryer', 'Grill',
            'Cutting Board', 'Knife Set', 'Cookware Set', 'Baking Sheet', 'Mixing Bowl',
            'Measuring Cups', 'Measuring Spoons', 'Colander', 'Strainer', 'Can Opener',
            'Spatula', 'Whisk', 'Tongs', 'Ladle', 'Turner',
            'Storage Container', 'Food Wrap', 'Aluminum Foil', 'Plastic Bags', 'Paper Towels',
            'Dish Soap', 'Sponge', 'Scrub Brush', 'Trash Bags', 'Cleaning Supplies'
        ]
        
        products = []
        for i in range(150):
            # Select random category and unit
            category = random.choice(categories)
            unit = random.choice(units)
            
            # Generate product name
            if i < len(product_names):
                name = product_names[i]
            else:
                name = f'Product {i+1}'
            
            # Generate SKU
            sku = f'STU{i+1:03d}'  # STU for STUDENT business
            
            # Generate random prices and quantities
            cost_price = Decimal(random.randint(5, 500))
            selling_price = cost_price * Decimal(random.uniform(1.2, 2.5)).quantize(Decimal('0.01'))
            quantity = Decimal(random.randint(1, 100))
            reorder_level = Decimal(random.randint(1, 20))
            
            product, created = Product.objects.get_or_create(
                business=business,
                sku=sku,
                defaults={
                    'name': name,
                    'category': category,
                    'unit': unit,
                    'description': f'High-quality {name.lower()} for everyday use',
                    'cost_price': cost_price,
                    'selling_price': selling_price,
                    'quantity': quantity,
                    'reorder_level': reorder_level,
                }
            )
            
            products.append(product)
        
        self.stdout.write(self.style.SUCCESS(f'Created/verified {len(products)} products'))
        
        # Create 50 customers for this business
        first_names = [
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
            'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph',
            'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy',
            'Daniel', 'Lisa', 'Matthew', 'Betty', 'Anthony', 'Helen', 'Mark', 'Sandra',
            'Donald', 'Donna', 'Steven', 'Carol', 'Paul', 'Ruth', 'Andrew', 'Sharon',
            'Joshua', 'Michelle', 'Kenneth', 'Laura', 'Kevin', 'Sarah', 'Brian', 'Kimberly',
            'George', 'Deborah', 'Timothy', 'Dorothy', 'Ronald', 'Lisa'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
            'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen',
            'Hill', 'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera',
            'Campbell', 'Mitchell', 'Carter', 'Roberts'
        ]
        
        customers = []
        for i in range(50):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f'{first_name.lower()}.{last_name.lower()}{i+1}@student.example.com'
            
            customer, created = Customer.objects.get_or_create(
                business=business,
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': f'+250-{random.randint(700, 799)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'address': f'{random.randint(100, 999)} Student Street, Kigali, Rwanda',
                    'company': f'{last_name} Student Services' if i % 4 == 0 else ''
                }
            )
            
            customers.append(customer)
        
        self.stdout.write(self.style.SUCCESS(f'Created/verified {len(customers)} customers'))
        
        # Delete existing sales for this business to start fresh
        Sale.objects.filter(business=business).delete()
        
        # Create 10 sales for this business
        payment_methods = ['cash', 'credit_card', 'mobile_money', 'bank_transfer']
        
        for i in range(10):
            # Select random customer
            customer = random.choice(customers)
            
            # Select random products (1-8 products per sale)
            num_products = random.randint(1, 8)
            selected_products = random.sample(products, min(num_products, len(products)))
            
            # Create sale
            sale_date = timezone.now() - timedelta(days=random.randint(0, 30))
            sale = Sale.objects.create(
                business=business,
                customer=customer,
                sale_date=sale_date,
                subtotal=Decimal('0.00'),
                tax=Decimal('0.00'),
                discount=Decimal('0.00'),
                total_amount=Decimal('0.00'),
                payment_method=random.choice(payment_methods),
                notes=f'Sample sale #{i+1} for {business.company_name}',
                created_at=sale_date
            )
            
            # Create sale items
            total_amount = Decimal('0.00')
            for product in selected_products:
                quantity = Decimal(random.randint(1, 5))
                unit_price = product.selling_price
                total_price = quantity * unit_price
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price
                )
                
                total_amount += total_price
            
            # Update sale totals
            sale.subtotal = total_amount
            sale.total_amount = total_amount
            sale.save()
            
            self.stdout.write(f'Created sale #{i+1} with {len(selected_products)} items')
        
        self.stdout.write(self.style.SUCCESS(f'Created {10} sales'))
        
        # Summary
        total_categories = Category.objects.filter(business=business).count()
        total_units = Unit.objects.filter(business=business).count()
        total_products = Product.objects.filter(business=business).count()
        total_customers = Customer.objects.filter(business=business).count()
        total_sales = Sale.objects.filter(business=business).count()
        total_sale_items = SaleItem.objects.filter(sale__business=business).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nData Summary for {user.username} ({business.company_name}):\n'
                f'Categories: {total_categories}\n'
                f'Units: {total_units}\n'
                f'Products: {total_products}\n'
                f'Customers: {total_customers}\n'
                f'Sales: {total_sales}\n'
                f'Sale Items: {total_sale_items}\n'
            )
        )