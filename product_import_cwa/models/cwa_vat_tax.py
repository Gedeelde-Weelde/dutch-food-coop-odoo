from odoo import api, fields, models


class CwaProductTax(models.Model):
    _name = "cwa.vat.tax"
    _description = "BTW Sale and Purchase Translations"
    _order = "btw"
    _rec_name = "description"

    btw = fields.Integer("BTW", required=True)
    description = fields.Char("Short Name", required=True)
    sale_tax = fields.Many2many(
        "account.tax", "cwa_sale_taxes_rel", "btw", string="Sales Tax"
    )
    purchase_tax = fields.Many2many(
        "account.tax", "cwa_purchase_taxes_rel", "btw", string="Purchases Tax"
    )

    @api.model
    def get_translated(self, btw):
        return self.search([("btw", "=", btw)], limit=1)
