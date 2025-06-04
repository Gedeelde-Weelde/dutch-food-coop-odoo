from odoo import models, fields


class BarcodeRule(models.Model):
    _inherit = 'barcode.rule'

    price_check_digit = fields.Boolean(
        string='Price Check Digit',
        default=False,
        help='Enable check digit validation for price-encoded barcodes'
    )
    price_check_digit_position = fields.Selection([
        ('end_price', 'At the end of the Price'),
        ('start_price', 'At the start of the Price'),
    ], string='Check Digit Position', default='start_price',
        help='Position of the check digit relative to the price value')

