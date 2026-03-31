from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    original_price = fields.Float(
        string="Original Price",
        digits="Product Price",
        readonly=True,
        default=0,
        help="Unit price before pricelist discount (product list price).",
    )
    discounted_price = fields.Float(
        string="Discounted Price",
        digits="Product Price",
        readonly=True,
        default=0,
        help="Unit price after pricelist discount.",
    )
    discount_total = fields.Monetary(
        string="Total Discount",
        store=True,
        readonly=True,
        default=0,
        currency_field="currency_id",
        help="Total discount amount: (original price − discounted price) × quantity.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Compute discount info when creating POS order lines."""
        lines = super().create(vals_list)
        for line in lines:
            line._compute_pricelist_discount_info()
        return lines

    def _compute_pricelist_discount_info(self):
        """Capture the original list price and the pricelist price."""
        for line in self:
            if not line.product_id or not line.order_id.pricelist_id:
                line.original_price = line.price_unit
                line.discounted_price = line.price_unit
                continue

            line.discounted_price = line.price_unit
            line.original_price = line.product_id.lst_price
            line.discount_total = (
                (line.original_price - line.discounted_price) * line.qty
            )
