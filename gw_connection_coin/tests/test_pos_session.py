from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase

CORE_VALIDATE_SESSION = (
    "odoo.addons.point_of_sale.models.pos_session.PosSession._validate_session"
)


class TestPosSessionAnonymization(TransactionCase):
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

    def _create_order(self, partner=None, account_move=None, lines=None, session=None):
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
        if lines is not None:
            vals["lines"] = lines
        return self.env["pos.order"].create(vals)

    def _add_payment(self, order, payment_method):
        self.env["pos.payment"].create(
            {
                "pos_order_id": order.id,
                "amount": 0.0,
                "payment_method_id": payment_method.id,
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

    def _close_session(self, session=None):
        # Stand-in for odoo core's _validate_session(): reaching its real
        # success path (`self.write({'state': 'closed'})`) requires a full,
        # balanced accounting move, which is out of scope here since these
        # tests exercise our anonymization hook, not core's accounting
        # logic. Patching core's implementation to just perform that state
        # transition lets us verify the hook fires exactly when core would
        # consider the close successful.
        session = session or self.pos_session

        def fake_validate_session(*args, **kwargs):
            session.write({"state": "closed"})
            return True

        with patch(CORE_VALIDATE_SESSION, side_effect=fake_validate_session):
            return session._validate_session()

    def test_partner_cleared_when_no_exemption_applies(self):
        order = self._create_order(partner=self.partner)
        self._close_session()
        self.assertEqual(order.partner_id.id, False)

    def test_partner_kept_with_account_move(self):
        invoice = self.env["account.move"].create({})
        order = self._create_order(partner=self.partner, account_move=invoice)
        self._close_session()
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_kept_with_connection_coin_line(self):
        order = self._create_order(
            partner=self.partner,
            lines=[self._order_line_vals(self.connection_coin_product)],
        )
        self._close_session()
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_kept_with_split_transactions_payment(self):
        session, payment_method = self._create_session_with_payment_method(
            split_transactions=True
        )
        order = self._create_order(partner=self.partner, session=session)
        self._add_payment(order, payment_method)
        self._close_session(session)
        self.assertEqual(order.partner_id, self.partner)

    def test_partner_cleared_with_non_split_transactions_payment(self):
        session, payment_method = self._create_session_with_payment_method(
            split_transactions=False
        )
        order = self._create_order(partner=self.partner, session=session)
        self._add_payment(order, payment_method)
        self._close_session(session)
        self.assertEqual(order.partner_id.id, False)

    def test_partner_untouched_until_session_actually_closes(self):
        # The behavior change itself: the partner must survive create() and
        # write() and only get cleared once the session is actually closed.
        order = self._create_order()
        order.write({"partner_id": self.partner.id})
        self.assertEqual(order.partner_id, self.partner)
        self._close_session()
        self.assertEqual(order.partner_id.id, False)

    def test_anonymization_skipped_when_session_close_does_not_succeed(self):
        # _validate_session() has an early-return path (balance mismatch)
        # that never reaches `state = 'closed'`; our hook must not
        # anonymize in that case.
        order = self._create_order(partner=self.partner)
        with patch(CORE_VALIDATE_SESSION, return_value=True):
            self.pos_session._validate_session()
        self.assertEqual(order.partner_id, self.partner)

    def test_anonymization_is_idempotent(self):
        order = self._create_order(partner=self.partner)
        self._close_session()
        self.assertEqual(order.partner_id.id, False)
        # Re-running on an already-anonymized, already-closed session (e.g.
        # a force-close retry) must not error.
        order._anonymize_after_session_close()
        self.assertEqual(order.partner_id.id, False)
