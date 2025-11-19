from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from products.models import Product, Category, Unit
from customers.models import Customer

User = get_user_model()


class POSTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", role="admin"
        )

        # Create test category and unit
        self.category = Category.objects.create(name="Test Category")
        self.unit = Unit.objects.create(name="Piece", symbol="pcs")

        # Create test products
        self.product1 = Product.objects.create(
            name="Test Product 1",
            sku="TP001",
            category=self.category,
            unit=self.unit,
            quantity=10,
            cost_price=5.00,
            selling_price=10.00,
        )

        self.product2 = Product.objects.create(
            name="Test Product 2",
            sku="TP002",
            category=self.category,
            unit=self.unit,
            quantity=5,
            cost_price=8.00,
            selling_price=15.00,
        )

        # Create test customer
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
        )

        # Create a client and log in
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_pos_view_loads(self):
        """Test that the POS view loads successfully"""
        response = self.client.get(reverse("sales:pos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Point of Sale")

    def test_product_display_in_pos(self):
        """Test that products are displayed in the POS view"""
        response = self.client.get(reverse("sales:pos"))
        self.assertContains(response, self.product1.name)
        self.assertContains(response, str(self.product1.selling_price))

    def test_add_product_to_cart(self):
        """Test adding a product to the cart via AJAX"""
        response = self.client.get(
            reverse(
                "sales:get_product_details", kwargs={"product_id": self.product1.id}
            )
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.product1.id)
        self.assertEqual(data["name"], self.product1.name)
        self.assertEqual(float(data["price"]), float(self.product1.selling_price))

    def test_process_pos_sale(self):
        """Test processing a POS sale"""
        sale_data = {
            "customer_id": self.customer.id,
            "payment_method": "cash",
            "discount": 0,
            "cart_items": [
                {
                    "id": self.product1.id,
                    "name": self.product1.name,
                    "price": str(self.product1.selling_price),
                    "quantity": 2,
                }
            ],
        }

        response = self.client.post(
            reverse("sales:process_pos_sale"),
            data=sale_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("sale_id", data)
