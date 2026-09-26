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
            for command, _id, line_vals in vals.get("lines") or []
            if command == 0
        ]
        if not product_ids:
            return False
        return bool(
            self.env["product.product"].search_count(
                [("id", "in", product_ids), ("is_connection_coin", "=", True)]
            )
        )

    def _has_split_transactions_payment(self):
        self.ensure_one()
        return bool(self.payment_ids.payment_method_id.filtered("split_transactions"))

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        # Odoo core's _order_fields() (used to build the vals passed to
        # create()/write() from _process_order()) never includes payment
        # info: the frontend's payments only reach the order afterwards,
        # here, via add_payment() on the raw 'statement_ids' data. So the
        # anonymization decision made in create()/write() is necessarily
        # made before a split_transactions payment can exist on the order,
        # and must be corrected once it does.
        result = super()._process_payment_lines(pos_order, order, pos_session, draft)
        if (
            not order.partner_id
            and pos_order.get("partner_id")
            and order._has_split_transactions_payment()
        ):
            order.partner_id = pos_order["partner_id"]
        return result

    def write(self, vals):
        result = super().write(vals)
        if vals.get("partner_id"):
            anonymizable = self.filtered(
                lambda order: not order.account_move
                and not order._has_split_transactions_payment()
            )
            if anonymizable:
                super(PosOrder, anonymizable).write({"partner_id": False})
        return result
