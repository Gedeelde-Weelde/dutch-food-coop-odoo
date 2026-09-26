from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _get_pos_ui_res_partner(self, params):
        # Add your custom fields to the fields list
        params["search_params"]["fields"].extend(
            [
                "cc_number",
                "cc_renewal_date",
                "cc_end_date",
                "cc_forgotten",
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

    def _validate_session(
        self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None
    ):
        result = super()._validate_session(
            balancing_account, amount_to_balance, bank_payment_method_diffs
        )
        if self.state == "closed":
            self.order_ids._anonymize_after_session_close()
        return result
