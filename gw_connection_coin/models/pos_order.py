from odoo import api, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("to_invoice") and not vals.get("account_move"):
                vals["partner_id"] = False
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if vals.get("partner_id"):
            uninvoiced = self.filtered(lambda order: not order.account_move)
            if uninvoiced:
                super(PosOrder, uninvoiced).write({"partner_id": False})
        return result
