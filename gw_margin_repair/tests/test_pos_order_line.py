from pickle import FALSE

from odoo import fields
from odoo.tests import TransactionCase


class TestPosOrderLineTotalCost(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create currency
        self.currency = self.env["res.currency"].create(
            {
                "name": "TEST",
                "symbol": "T$",
                "rate": 1.0,
            }
        )

        # Create product with standard_price and cost_currency_id
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "standard_price": 10.0,
                "list_price": 20.0,
                "cost_currency_id": self.currency.id,
            }
        )

        # Create POS config with minimal required fields
        self.pos_config = self.env["pos.config"].create(
            {
                "name": "Test Config",
            }
        )

        # Create POS session
        self.pos_session = self.env["pos.session"].create(
            {
                "config_id": self.pos_config.id,
            }
        )

        # Create POS order with required fields
        self.pos_order = self.env["pos.order"].create(
            {
                "session_id": self.pos_session.id,
                "date_order": fields.Datetime.now(),
                "company_id": self.env.company.id,
                "amount_tax": 0.0,
                "amount_total": 30.0,
                "amount_paid": 0.0,
                "amount_return": 0.0,
            }
        )

        # Create POS order line
        self.order_line = self.env["pos.order.line"].create(
            {
                "order_id": self.pos_order.id,
                "product_id": self.product.id,
                "qty": 2.0,
                "name": "Test Line",
                "price_subtotal": 30.0,
                "price_subtotal_incl": 30.0,
            }
        )

    def test_compute_total_cost_standard_product(self):
        total_cost = self.order_line._compute_total_cost(FALSE)
        self.assertEqual(total_cost, 60.0)
