from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

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

    @api.depends("original_price", "discounted_price", "product_uom_qty")
    def _compute_discount_total(self):
        for line in self:
            line.discount_total = (
                (line.original_price - line.discounted_price) * line.product_uom_qty
            )

    def _update_pricelist_discount_info(self):
        """Capture the original list price and the pricelist price."""
        for line in self:
            if not line.product_id or not line.order_id.pricelist_id:
                line.original_price = line.price_unit
                line.discounted_price = line.price_unit
                continue

            # --- Original price: product list price, converted to line UoM ---
            original = line.product_id.lst_price
            if (
                line.product_uom
                and line.product_id.uom_id
                and line.product_id.uom_id != line.product_uom
            ):
                original = line.product_id.uom_id._compute_price(
                    original, line.product_uom
                )

            # --- Pricelist price: what the customer actually pays per unit ---
            pricelist = line.order_id.pricelist_id
            pricelist_price = pricelist._get_product_price(
                line.product_id,
                line.product_uom_qty or 1.0,
                uom=line.product_uom,
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

    # --- Hook into the standard onchange methods ---

    @api.onchange("product_id")
    def product_id_change(self):
        result = super().product_id_change()
        self._update_pricelist_discount_info()
        return result

    @api.onchange("product_uom", "product_uom_qty")
    def product_uom_change(self):
        result = super().product_uom_change()
        self._update_pricelist_discount_info()
        return result
