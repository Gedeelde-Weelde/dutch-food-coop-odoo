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
