from odoo import fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _compute_total_cost(self, stock_moves):  # pylint: disable=W8110
        """
        Compute the total cost of the order lines.
        :param stock_moves: recordset of `stock.move`, used for fifo/avco lines
        """
        for line in self.filtered(lambda ln: not ln.is_total_cost_computed):
            product = line.product_id
            if product.list_price > 0 and line.price_unit != product.list_price:
                product_cost = (
                    line.price_unit / product.list_price
                ) * product.standard_price
                line.total_cost = line.qty * product.cost_currency_id._convert(
                    from_amount=product_cost,
                    to_currency=line.currency_id,
                    company=line.company_id or self.env.company,
                    date=line.order_id.date_order or fields.Date.today(),
                    round=False,
                )
                line.is_total_cost_computed = True
        # Call super to calculate the uncalculated lines
        super()._compute_total_cost(stock_moves)
