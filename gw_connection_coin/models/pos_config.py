from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    member_connection_coin_product_id = fields.Many2one(
        "product.product", string="Member Connection Coin Product"
    )
    non_member_connection_coin_product_id = fields.Many2one(
        "product.product", string="Non-Member Connection Coin Product"
    )

    @api.constrains(
        "member_connection_coin_product_id", "non_member_connection_coin_product_id"
    )
    def _check_connection_coin_products_are_marked(self):
        for config in self:
            for product in (
                config.member_connection_coin_product_id,
                config.non_member_connection_coin_product_id,
            ):
                if product and not product.is_connection_coin:
                    raise ValidationError(
                        _("%s must be flagged as a Connection Coin Product.")
                        % product.display_name
                    )
