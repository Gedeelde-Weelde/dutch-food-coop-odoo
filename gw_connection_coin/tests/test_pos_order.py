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

    def _create_order(self, partner=None, lines=None):
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
        if lines is not None:
            vals["lines"] = lines
        return self.env["pos.order"].create(vals)

    def test_partner_untouched_by_create(self):
        # Anonymization is now deferred entirely to session close; create()
        # must no longer null the partner out, regardless of invoice/coin
        # status.
        order = self._create_order(partner=self.partner)
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_untouched_by_write(self):
        order = self._create_order()
        order.write({"partner_id": self.partner.id})
        self.assertEqual(order.partner_id, self.partner)

    def test_create_with_no_lines_does_not_crash(self):
        # The POS frontend allows validating an order with zero orderlines,
        # which odoo core's _order_fields then serializes as `'lines':
        # False` rather than omitting the key or sending `[]`.
        order = self._create_order(partner=self.partner, lines=False)
        self.assertEqual(order.partner_id, self.partner)

    def test_cc_renewal_date_advanced_one_year_on_connection_coin_order(self):
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": fields.Date.from_string("2020-01-01"),
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
            }
        )
        self._create_order(
            partner=self.partner,
            lines=[self._order_line_vals(self.connection_coin_product)],
        )
        self.assertEqual(
            self.partner.cc_renewal_date, fields.Date.from_string("2027-01-01")
        )

    def test_cc_renewal_date_unchanged_on_regular_order(self):
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": fields.Date.from_string("2020-01-01"),
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
            }
        )
        self._create_order(
            partner=self.partner,
            lines=[self._order_line_vals(self.regular_product)],
        )
        self.assertEqual(
            self.partner.cc_renewal_date, fields.Date.from_string("2026-01-01")
        )