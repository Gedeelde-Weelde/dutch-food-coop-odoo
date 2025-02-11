from odoo import api, fields, models


class CwaProductBrands(models.Model):
    _name = "cwa.product.brands"
    _description = "Product Brands"
    _order = "source_value"
    _rec_name = "source_value"

    source_value = fields.Char(size=64, required=True)
    destination_value = fields.Many2one(
        "product.brand", "Brand Name", ondelete="cascade"
    )

    _sql_constraints = [
        (
            "cwa_product_brand_unique",
            "unique(source_value)",
            "A brand can only have one translation.",
        )
    ]

    @api.model
    def get_translated(self, source):
        return self.search([("source_value", "=ilike", source)], limit=1)


class ProductBrand(models.Model):
    _inherit = "product.brand"

    _sql_constraints = [
        ("product_brand_name_unique", "unique(name)", "This brand name already exist.")
    ]
