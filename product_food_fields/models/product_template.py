from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ingredients = fields.Text(help="Ingredients in the product")
    origin = fields.Char(help="Land where the product is produced, an ISO 3166 code")
    usage_tips = fields.Char(help="Usage tips")
    # TODO: rename field
    days_until_expiry = fields.Integer(help="Days until expiration")
    # TODO: rename field
    days_until_bad_taste = fields.Integer(help="Days until bad test")
    storage_temperature = fields.Integer(help="Storage temperature in Celcius")
    product_quality_id = fields.Many2one(
        "product_food_fields.product_quality", string="Product quality"
    )
