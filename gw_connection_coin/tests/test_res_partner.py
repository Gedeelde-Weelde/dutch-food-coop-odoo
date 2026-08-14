from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import TransactionCase


class TestResPartner(TransactionCase):
    def test_barcode_set_from_cc_nummer(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_cc_nummer": "711",
            }
        )
        self.assertEqual(partner.barcode, "04200711")

    def test_barcode_set_from_cc_nummer_on_write(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        partner.write({"x_cc_nummer": "711"})
        self.assertEqual(partner.barcode, "04200711")

    def test_barcode_cleared_when_cc_nummer_removed(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_cc_nummer": "711",
            }
        )
        partner.write({"x_cc_nummer": False})
        self.assertEqual(partner.barcode, False)

    def test_end_connection_coin_sets_einde_to_verleng(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_cc_nummer": "711",
                "x_cc_verleng": fields.Date.from_string("2026-01-01"),
            }
        )
        partner.end_connection_coin()
        self.assertEqual(partner.x_cc_einde, partner.x_cc_verleng)

    def test_extend_connection_coin_advances_verleng_by_one_year(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_cc_verleng": fields.Date.from_string("2026-01-01"),
            }
        )
        partner.extend_connection_coin()
        self.assertEqual(partner.x_cc_verleng, fields.Date.from_string("2027-01-01"))

    def test_extend_connection_coin_noop_without_verleng(self):
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        partner.extend_connection_coin()
        self.assertEqual(partner.x_cc_verleng, False)

    def test_mark_connection_coin_forgotten_increments_count(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_cc_nummer": "711",
            }
        )
        self.assertEqual(partner.x_cc_vergeten, 0)
        result = partner.mark_connection_coin_forgotten()
        self.assertEqual(partner.x_cc_vergeten, 1)
        self.assertEqual(result, 1)
        partner.mark_connection_coin_forgotten()
        self.assertEqual(partner.x_cc_vergeten, 2)

    def test_is_member_false_when_membership_fields_absent(self):
        # On a database without the manually-added x_lid_begin/x_lid_einde
        # fields (e.g. this test database), is_member must degrade to False
        # instead of raising.
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.assertFalse(partner.is_member)


class TestResPartnerMembership(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Simulate the pre-existing manual (Studio-added) x_lid_begin/
        # x_lid_einde fields that _compute_is_member reads defensively,
        # without gw_connection_coin declaring them in code (see the
        # comment above _compute_is_member for why).
        model_id = cls.env["ir.model"]._get_id("res.partner")
        cls.env["ir.model.fields"].create(
            [
                {
                    "name": "x_lid_begin",
                    "field_description": "Lidmaatschap Startdatum",
                    "model_id": model_id,
                    "ttype": "date",
                },
                {
                    "name": "x_lid_einde",
                    "field_description": "Lidmaatschap Einddatum",
                    "model_id": model_id,
                    "ttype": "date",
                },
            ]
        )

    def test_is_member_true_within_range(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_lid_begin": fields.Date.today() - relativedelta(days=1),
                "x_lid_einde": fields.Date.today() + relativedelta(days=1),
            }
        )
        self.assertTrue(partner.is_member)

    def test_is_member_true_without_end_date(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_lid_begin": fields.Date.today() - relativedelta(days=1),
            }
        )
        self.assertTrue(partner.is_member)

    def test_is_member_false_before_begin(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_lid_begin": fields.Date.today() + relativedelta(days=1),
            }
        )
        self.assertFalse(partner.is_member)

    def test_is_member_false_after_end(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_lid_begin": fields.Date.today() - relativedelta(days=10),
                "x_lid_einde": fields.Date.today() - relativedelta(days=1),
            }
        )
        self.assertFalse(partner.is_member)

    def test_is_member_false_without_begin_date(self):
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.assertFalse(partner.is_member)
