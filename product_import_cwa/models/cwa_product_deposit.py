from odoo import api, fields, models


class CwaProductDeposit(models.Model):
    _name = "cwa.product.deposit"
    _description = "Product Deposit"

    source_deposit_price = fields.Float(
        required=True,
        help="Price of the product deposit.",
    )
    deposit_product_id = fields.Many2one(
        "product.template",
        string="Linked Product",
        required=True,
        domain=[("is_deposit", "=", True)],
        help="Select a product where the deposit is true.",
    )

    @api.model
    def get_translated(self, deposit):
        return self.search([("source_deposit_price", "=", deposit)], limit=1)
