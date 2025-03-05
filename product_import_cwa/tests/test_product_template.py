from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_template = self.env["product.template"]
        self.tax_model = self.env["account.tax"]

        self.test_tax_21 = self.tax_model.create({
            "name": "Test Tax 21%",
            "amount": 21,
            "amount_type": "percent",
            "price_include": True,
        })

        self.test_tax_9 = self.tax_model.create({
            "name": "Test Tax 9%",
            "amount": 9,
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
            "taxes_id": [(4, self.test_tax_21.id)]  # Add tax
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

    def test_margin_calculation_multiple_products_different_taxes(self):
        """Test margin calculation for multiple products with different taxes using recordset"""
        # Create multiple products at once as a recordset
        products = self.product_template.create([
            {
                "name": "Test Product 1",
                "list_price": 121.0,  # Sales price including 21% tax
                "standard_price": 80.0,  # Cost price
                "taxes_id": [(4, self.test_tax_21.id)]  # Add 21% tax
            },
            {
                "name": "Test Product 2",
                "list_price": 109.0,  # Sales price including 9% tax
                "standard_price": 70.0,  # Cost price
                "taxes_id": [(4, self.test_tax_9.id)]  # Add 9% tax
            }
        ])

        # Force computation of margins for the entire recordset
        products._compute_margin()

        # Get products from recordset
        product1 = products[0]
        product2 = products[1]

        # Product 1: Price without tax: 121 / 1.21 = 100
        # Expected margin: (100 - 80) / 100 = 0.2 (20%)
        self.assertAlmostEqual(product1.margin, 0.2, places=2)

        # Product 2: Price without tax: 109 / 1.09 = 100
        # Expected margin: (100 - 70) / 100 = 0.3 (30%)
        self.assertAlmostEqual(product2.margin, 0.3, places=2)

        # Test that computing margins as a recordset gives same results
        margins = products.mapped('margin')
        self.assertAlmostEqual(margins[0], 0.2, places=2)
        self.assertAlmostEqual(margins[1], 0.3, places=2)
