from pickle import FALSE

from odoo import fields
from odoo.tests import TransactionCase

list_order_price = 15.0
standard_price = 38.5
list_price = 58.9


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
                "standard_price": standard_price,
                "list_price": list_price,
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
                "amount_total": list_order_price,
                "amount_paid": 0.0,
                "amount_return": 0.0,
            }
        )

    def test_compute_total_cost_standard_product(self):
        # Create POS order line
        self.order_line = self.env["pos.order.line"].create(
            {
                "order_id": self.pos_order.id,
                "product_id": self.product.id,
                "qty": 1.0,
                "name": "Test Line",
                "price_subtotal": 13.76,
                "price_subtotal_incl": list_order_price,
                "price_unit": list_order_price,
            }
        )
        self.order_line._compute_total_cost(FALSE)
        self.assertEqual(self.order_line.total_cost, 9.8)

    def test_compute_total_cost_standard_product_mulitple(self):
        # Create POS order line
        self.order_line = self.env["pos.order.line"].create(
            {
                "order_id": self.pos_order.id,
                "product_id": self.product.id,
                "qty": 2.0,
                "name": "Test Line",
                "price_subtotal": 27.52,
                "price_subtotal_incl": list_order_price * 2,
                "price_unit": list_order_price,
            }
        )
        self.order_line._compute_total_cost(FALSE)
        self.assertEqual(self.order_line.total_cost, 19.61)

    def test_no_division_by_zero(self):
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "standard_price": 0.0,
                "list_price": 0.0,
                "cost_currency_id": self.currency.id,
            }
        )
        self.order_line = self.env["pos.order.line"].create(
            {
                "order_id": self.pos_order.id,
                "product_id": self.product.id,
                "qty": 1.0,
                "name": "Test Line",
                "price_subtotal": 0.0,
                "price_subtotal_incl": 0.0,
                "price_unit": -0.5,
            }
        )
        self.order_line._compute_total_cost(FALSE)
        self.assertEqual(self.order_line.total_cost, 0.0)
