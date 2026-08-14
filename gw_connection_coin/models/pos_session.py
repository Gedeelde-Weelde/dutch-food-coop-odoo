from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _get_pos_ui_res_partner(self, params):
        # Add your custom fields to the fields list
        params["search_params"]["fields"].extend(
            [
                "x_cc_nummer",
                "x_cc_verleng",
                "x_cc_einde",
                "x_cc_vergeten",
                "is_member",
            ]
        )
        return super()._get_pos_ui_res_partner(params)

    def _get_pos_ui_product_product(self, params):
        params["search_params"]["fields"].extend(
            [
                "is_connection_coin",
            ]
        )
        return super()._get_pos_ui_product_product(params)
