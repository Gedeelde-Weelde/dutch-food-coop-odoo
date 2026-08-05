from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_connection_coin = fields.Boolean(string="Connection Coin Product")
