from odoo import models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _compute_total_cost(self, stock_moves):
        return super()._compute_total_cost(stock_moves)
