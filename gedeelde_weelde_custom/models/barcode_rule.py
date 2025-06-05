from odoo import models, fields


class BarcodeRule(models.Model):
    _inherit = 'barcode.rule'

    price_check_digit = fields.Boolean(
        string='Price Check Digit',
        default=False,
        help='Enable check digit validation for price-encoded barcodes'
    )
