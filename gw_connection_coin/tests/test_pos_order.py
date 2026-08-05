from odoo import fields
from odoo.tests import TransactionCase


class TestPosOrderAnonymization(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner = self.env["res.partner"].create({"name": "Test Customer"})
        self.pos_config = self.env["pos.config"].create({"name": "Test Config"})
        self.pos_session = self.env["pos.session"].create(
            {"config_id": self.pos_config.id}
        )
        self.connection_coin_product = self.env["product.product"].create(
            {"name": "Connection Coin", "is_connection_coin": True}
        )
        self.regular_product = self.env["product.product"].create(
            {"name": "Regular Product"}
        )

    def _order_line_vals(self, product):
        return (
            0,
            0,
            {
                "name": product.name,
                "product_id": product.id,
                "price_subtotal": 0.0,
                "price_subtotal_incl": 0.0,
            },
        )

    def _create_order(
        self, partner=None, account_move=None, to_invoice=None, lines=None
    ):
        vals = {
            "session_id": self.pos_session.id,
            "date_order": fields.Datetime.now(),
            "company_id": self.env.company.id,
            "amount_tax": 0.0,
            "amount_total": 0.0,
            "amount_paid": 0.0,
            "amount_return": 0.0,
        }
        if partner is not None:
            vals["partner_id"] = partner.id
        if account_move is not None:
            vals["account_move"] = account_move.id
        if to_invoice is not None:
            vals["to_invoice"] = to_invoice
        if lines is not None:
            vals["lines"] = lines
        return self.env["pos.order"].create(vals)

    def test_partner_cleared_on_create_without_invoice(self):
        order = self._create_order(partner=self.partner)
        self.assertEqual(order.partner_id.id, False)

    def test_partner_kept_on_create_with_to_invoice_flag(self):
        order = self._create_order(partner=self.partner, to_invoice=True)
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_kept_on_create_with_invoice(self):
        invoice = self.env["account.move"].create({})
        order = self._create_order(partner=self.partner, account_move=invoice)
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_cleared_on_write_without_invoice(self):
        order = self._create_order()
        order.write({"partner_id": self.partner.id})
        self.assertEqual(order.partner_id.id, False)

    def test_partner_kept_on_write_with_invoice(self):
        invoice = self.env["account.move"].create({})
        order = self._create_order(account_move=invoice)
        order.write({"partner_id": self.partner.id})
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_kept_on_create_with_connection_coin_product(self):
        order = self._create_order(
            partner=self.partner,
            lines=[self._order_line_vals(self.connection_coin_product)],
        )
        self.assertEqual(order.partner_id, self.partner)

    def test_x_cc_verleng_advanced_one_year_on_connection_coin_order(self):
        self.partner.x_cc_verleng = fields.Date.from_string("2026-01-01")
        self._create_order(
            partner=self.partner,
            lines=[self._order_line_vals(self.connection_coin_product)],
        )
        self.assertEqual(
            self.partner.x_cc_verleng, fields.Date.from_string("2027-01-01")
        )

    def test_x_cc_verleng_unchanged_on_regular_order(self):
        self.partner.x_cc_verleng = fields.Date.from_string("2026-01-01")
        self._create_order(
            partner=self.partner,
            lines=[self._order_line_vals(self.regular_product)],
        )
        self.assertEqual(
            self.partner.x_cc_verleng, fields.Date.from_string("2026-01-01")
        )
