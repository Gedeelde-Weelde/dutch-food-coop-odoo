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
        # account.move.create({}) needs a 'general' journal to pick as its
        # default; a bare test company has no chart of accounts (no
        # l10n_* module is installed), so none exists unless we add one.
        if not self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id), ("type", "=", "general")],
            limit=1,
        ):
            self.env["account.journal"].create(
                {
                    "name": "Miscellaneous Operations",
                    "code": "MISC",
                    "type": "general",
                    "company_id": self.env.company.id,
                }
            )

    def _create_session_with_payment_method(self, split_transactions):
        # pos.config forbids changing payment_method_ids while a session is
        # open (see setUp's self.pos_session), so the payment method must be
        # attached to a config at creation time, on a separate session.
        payment_method = self.env["pos.payment.method"].create(
            {
                "name": "Test Payment Method",
                "split_transactions": split_transactions,
            }
        )
        pos_config = self.env["pos.config"].create(
            {
                "name": "Test Config With Payment Method",
                "payment_method_ids": [(4, payment_method.id)],
            }
        )
        session = self.env["pos.session"].create({"config_id": pos_config.id})
        return session, payment_method

    def _add_payment(self, order, payment_method):
        self.env["pos.payment"].create(
            {
                "pos_order_id": order.id,
                "amount": 0.0,
                "payment_method_id": payment_method.id,
            }
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

    def _call_process_payment_lines(self, order, payment_method, partner=None, draft=False):
        # Mirrors how odoo core's _process_order() calls this method: with
        # the raw ui order dict (here just the keys _process_payment_lines
        # and _payment_fields actually read) as first argument, and the
        # already created/written pos.order record as second argument.
        ui_order = {
            "statement_ids": [
                (
                    0,
                    0,
                    {
                        "amount": 0.0,
                        "name": fields.Datetime.now(),
                        "payment_method_id": payment_method.id,
                    },
                )
            ],
            "amount_return": 0.0,
        }
        if partner is not None:
            ui_order["partner_id"] = partner.id
        self.env["pos.order"]._process_payment_lines(
            ui_order, order, order.session_id, draft
        )

    def _create_order(
        self, partner=None, account_move=None, to_invoice=None, lines=None, session=None
    ):
        vals = {
            "session_id": (session or self.pos_session).id,
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

    def test_partner_kept_on_write_with_split_transactions_payment_method(self):
        session, payment_method = self._create_session_with_payment_method(
            split_transactions=True
        )
        order = self._create_order(session=session)
        self._add_payment(order, payment_method)
        order.write({"partner_id": self.partner.id})
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_cleared_on_write_with_non_split_transactions_payment_method(self):
        session, payment_method = self._create_session_with_payment_method(
            split_transactions=False
        )
        order = self._create_order(session=session)
        self._add_payment(order, payment_method)
        order.write({"partner_id": self.partner.id})
        self.assertEqual(order.partner_id.id, False)

    def test_partner_restored_after_process_payment_lines_with_split_transactions_payment_method(
        self,
    ):
        # This is the real-world path: odoo core's _order_fields() (used to
        # build create()/write() vals from _process_order()) never includes
        # payment info, so the payment method is unknown to create()/write()
        # at anonymization time. Payments only get attached afterwards, via
        # _process_payment_lines(), which is where the partner must be
        # restored instead.
        session, payment_method = self._create_session_with_payment_method(
            split_transactions=True
        )
        order = self._create_order(session=session)
        self.assertEqual(order.partner_id.id, False)
        self._call_process_payment_lines(order, payment_method, partner=self.partner)
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_stays_cleared_after_process_payment_lines_with_non_split_transactions_payment_method(
        self,
    ):
        session, payment_method = self._create_session_with_payment_method(
            split_transactions=False
        )
        order = self._create_order(session=session)
        self._call_process_payment_lines(order, payment_method, partner=self.partner)
        self.assertEqual(order.partner_id.id, False)

    def test_partner_kept_on_create_with_connection_coin_product(self):
        order = self._create_order(
            partner=self.partner,
            lines=[self._order_line_vals(self.connection_coin_product)],
        )
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

    def test_partner_cleared_on_create_with_no_lines(self):
        # The POS frontend allows validating an order with zero orderlines
        # as long as it isn't marked to_invoice (PaymentScreen only blocks
        # that combination). Odoo core's _order_fields then serializes such
        # an order as `'lines': False` rather than omitting the key or
        # sending `[]`, which must not crash order creation.
        order = self._create_order(partner=self.partner, lines=False)
        self.assertEqual(order.partner_id.id, False)

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
