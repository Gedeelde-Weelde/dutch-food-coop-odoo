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
