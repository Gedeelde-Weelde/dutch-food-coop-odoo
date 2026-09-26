from odoo import api, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.partner_id and order.lines.product_id.filtered(
                "is_connection_coin"
            ):
                order.partner_id.extend_connection_coin()
        return orders

    def _has_split_transactions_payment(self):
        self.ensure_one()
        return bool(self.payment_ids.payment_method_id.filtered("split_transactions"))

    def _should_keep_partner(self):
        self.ensure_one()
        return bool(
            self.account_move
            or self.lines.product_id.filtered("is_connection_coin")
            or self._has_split_transactions_payment()
        )

    def _anonymize_after_session_close(self):
        anonymizable = self.filtered(
            lambda order: order.partner_id and not order._should_keep_partner()
        )
        if anonymizable:
            anonymizable.write({"partner_id": False})