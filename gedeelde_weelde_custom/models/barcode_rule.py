from odoo import fields, models


class BarcodeRule(models.Model):
    _inherit = "barcode.rule"

    price_check_digit = fields.Boolean(
        default=False,
        help="Enable check digit validation for price-encoded barcodes",
    )
