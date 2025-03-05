from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_template = self.env["product.template"]
        self.tax_model = self.env["account.tax"]

        self.test_tax = self.tax_model.create({
            "name": "Test Tax 21%",
            "amount": 21,
            "amount_type": "percent",
            "price_include": True,
        })

    def test_margin_calculation_without_tax(self):
        """Test margin calculation without taxes"""
        product = self.product_template.create({
            "name": "Test Product",
            "list_price": 100.0,  # Sales price
            "standard_price": 80.0,  # Cost price
            "taxes_id": [(5, 0, 0)]  # Clear taxes
        })

        # Expected margin: (100 - 80) / 100 = 0.2 (20%)
        self.assertEqual(product.margin, 0.2)

    def test_margin_calculation_with_tax(self):
        """Test margin calculation with taxes"""
        product = self.product_template.create({
            "name": "Test Product with Tax",
            "list_price": 121.0,  # Sales price including 21% tax
            "standard_price": 80.0,  # Cost price
            "taxes_id": [(4, self.test_tax.id)]  # Add tax
        })

        # Price without tax: 121 / 1.21 = 100
        # Expected margin: (100 - 80) / 100 = 0.2 (20%)
        self.assertAlmostEqual(product.margin, 0.2, places=2)

    def test_margin_calculation_zero_prices(self):
        """Test margin calculation with zero prices"""
        product = self.product_template.create({
            "name": "Zero Price Product",
            "list_price": 0.0,
            "standard_price": 0.0,
            "taxes_id": [(5, 0, 0)]
        })

        self.assertEqual(product.margin, 0.0)

    def test_margin_calculation_zero_sales_price(self):
        product = self.product_template.create({
            "name": "Zero Sales Price Product",
            "list_price": 0.0,
            "standard_price": 10.0,
            "taxes_id": [(5, 0, 0)]
        })

        self.assertEqual(product.margin, 0.0)
