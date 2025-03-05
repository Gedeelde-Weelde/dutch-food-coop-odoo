from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_template = self.env["product.template"]
        self.tax_model = self.env["account.tax"]

        self.test_tax_21 = self.tax_model.create(
            {
                "name": "Test Tax 21%",
                "amount": 21,
                "amount_type": "percent",
                "price_include": True,
            }
        )

        self.test_tax_9 = self.tax_model.create(
            {
                "name": "Test Tax 9%",
                "amount": 9,
                "amount_type": "percent",
                "price_include": True,
            }
        )

        self.expected_margins = {
            "product1": 0.2,  # (100 - 80) / 100
            "product2": 0.3,  # (100 - 70) / 100
        }

    def test_margin_calculation_without_tax(self):
        """Test margin calculation without taxes"""
        product = self.product_template.create(
            {
                "name": "Test Product",
                "list_price": 100.0,  # Sales price
                "standard_price": 80.0,  # Cost price
                "taxes_id": [(5, 0, 0)],  # Clear taxes
            }
        )

        # Expected margin: (100 - 80) / 100 = 0.2 (20%)
        self.assertEqual(product.margin, 0.2)

    def test_margin_calculation_with_tax(self):
        """Test margin calculation with taxes"""
        product = self.product_template.create(
            {
                "name": "Test Product with Tax",
                "list_price": 121.0,  # Sales price including 21% tax
                "standard_price": 80.0,  # Cost price
                "taxes_id": [(4, self.test_tax_21.id)],  # Add tax
            }
        )

        # Price without tax: 121 / 1.21 = 100
        # Expected margin: (100 - 80) / 100 = 0.2 (20%)
        self.assertAlmostEqual(product.margin, 0.2, places=2)

    def test_margin_calculation_zero_prices(self):
        """Test margin calculation with zero prices"""
        product = self.product_template.create(
            {
                "name": "Zero Price Product",
                "list_price": 0.0,
                "standard_price": 0.0,
                "taxes_id": [(5, 0, 0)],
            }
        )

        self.assertEqual(product.margin, 0.0)

    def test_margin_calculation_zero_sales_price(self):
        product = self.product_template.create(
            {
                "name": "Zero Sales Price Product",
                "list_price": 0.0,
                "standard_price": 10.0,
                "taxes_id": [(5, 0, 0)],
            }
        )

        self.assertEqual(product.margin, 0.0)

    def _create_test_product(self, product_type="product1"):
        products = {
            "product1": {
                "name": "Test Product 1",
                "list_price": 121.0,
                "standard_price": 80.0,
                "taxes_id": [(4, self.test_tax_21.id)],
            },
            "product2": {
                "name": "Test Product 2",
                "list_price": 109.0,
                "standard_price": 70.0,
                "taxes_id": [(4, self.test_tax_9.id)],
            },
        }
        return self.product_template.create(products[product_type])

    def test_margin_calculation_product_with_21_tax(self):
        """Test margin calculation for product with 21% tax"""
        product = self._create_test_product("product1")
        product._compute_margin()
        self.assertAlmostEqual(
            product.margin, self.expected_margins["product1"], places=2
        )

    def test_margin_calculation_product_with_9_tax(self):
        """Test margin calculation for product with 9% tax"""
        product = self._create_test_product("product2")
        product._compute_margin()
        self.assertAlmostEqual(
            product.margin, self.expected_margins["product2"], places=2
        )

    def test_margin_calculation_with_different_taxes_in_recordset(self):
        """Test margin calculation in recordset with different taxes (21% and 9%)"""
        # Create products in reverse tax order to ensure tax handling is correct
        product2 = self._create_test_product("product2")  # 9% tax
        product1 = self._create_test_product("product1")  # 21% tax
        products = product2 + product1
        products._compute_margin()
        # Test second product's margin (21% tax) to verify tax calculation in recordset
        self.assertAlmostEqual(
            products.mapped("margin")[1], self.expected_margins["product1"], places=2
        )
