from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_bio_basic = fields.Boolean(default=False)
    is_batch = fields.Boolean(default=False)
