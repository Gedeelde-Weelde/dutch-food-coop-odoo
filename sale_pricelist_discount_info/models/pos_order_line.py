from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    original_price = fields.Float(
        string="Original Price",
        digits="Product Price",
        store=True,
        readonly=True,
        help="Unit price before pricelist discount (product list price).",
    )
    discounted_price = fields.Float(
        string="Discounted Price",
        digits="Product Price",
        store=True,
        readonly=True,
        help="Unit price after pricelist discount.",
    )
    discount_total = fields.Monetary(
        string="Total Discount",
        store=True,
        readonly=True,
        compute="_compute_discount_total",
        currency_field="currency_id",
        help="Total discount amount: (original price − discounted price) × quantity.",
    )

    @api.depends("original_price", "discounted_price", "qty")
    def _compute_discount_total(self):
        for line in self:
            line.discount_total = (
                (line.original_price - line.discounted_price) * line.qty
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

            # --- Original price: product list price ---
            original = line.product_id.lst_price

            # --- Pricelist price: what the customer actually pays per unit ---
            pricelist = line.order_id.pricelist_id
            pricelist_price = pricelist._get_product_price(
                line.product_id,
                line.qty or 1.0,
                date=line.order_id.date_order,
            )

            line.original_price = original

            if pricelist.discount_policy == "without_discount":
                # In this mode Odoo keeps price_unit = list price and fills
                # the native discount % field. Compute the effective price.
                line.discounted_price = original * (
                    1.0 - (line.discount or 0.0) / 100.0
                )
            else:
                # "with_discount" (default): price_unit IS the discounted
                # price, native discount field is 0.
                line.discounted_price = pricelist_price
