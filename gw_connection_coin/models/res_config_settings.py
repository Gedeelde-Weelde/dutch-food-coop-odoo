from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_member_connection_coin_product_id = fields.Many2one(
        related="pos_config_id.member_connection_coin_product_id", readonly=False
    )
    pos_non_member_connection_coin_product_id = fields.Many2one(
        related="pos_config_id.non_member_connection_coin_product_id", readonly=False
    )
