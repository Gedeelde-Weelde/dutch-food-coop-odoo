from odoo import api, fields, models


class CwaProductDeposit(models.Model):
    _name = "cwa.product.deposit"
    _description = "Product Deposit"

    source_deposit_price = fields.Float(
        string="Source Deposit Price",
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
