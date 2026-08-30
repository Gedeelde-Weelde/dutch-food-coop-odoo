from odoo import api, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        has_connection_coin = [
            self._vals_has_connection_coin(vals) for vals in vals_list
        ]
        for vals, connection_coin in zip(vals_list, has_connection_coin, strict=False):
            if (
                not vals.get("to_invoice")
                and not vals.get("account_move")
                and not connection_coin
            ):
                vals["partner_id"] = False
        orders = super().create(vals_list)
        for order, connection_coin in zip(orders, has_connection_coin, strict=False):
            if connection_coin and order.partner_id:
                order.partner_id.extend_connection_coin()
        return orders

    def _vals_has_connection_coin(self, vals):
        product_ids = [
            line_vals.get("product_id")
            for command, _id, line_vals in vals.get("lines", [])
            if command == 0
        ]
        if not product_ids:
            return False
        return bool(
            self.env["product.product"].search_count(
                [("id", "in", product_ids), ("is_connection_coin", "=", True)]
            )
        )

    def write(self, vals):
        result = super().write(vals)
        if vals.get("partner_id"):
            uninvoiced = self.filtered(lambda order: not order.account_move)
            if uninvoiced:
                super(PosOrder, uninvoiced).write({"partner_id": False})
        return result
