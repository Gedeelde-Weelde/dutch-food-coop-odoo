from odoo import fields, models


class CwaProductImportBrands(models.TransientModel):
    _name = "cwa.product.import.brands"
    _description = "Wizard for product translations"

    def _default_brand_ids(self):
        # for each cwa product, determine corresponding source and target brand
        cwa_product_ids = list(set(self.env.context.get("active_ids", [])))
        brand_ids = []
        brands = []
        for this in self.env["cwa.product"].browse(cwa_product_ids):
            trans = self.env["cwa.product.brands"].get_translated(this.merk)
            if not trans and this.merk not in brands:
                brands.append(this.merk)
                brand_ids.append(
                    (
                        0,
                        0,
                        {
                            "cwa_product_id": this.id,
                            "source_brand": this.merk,
                            "target_brand": this.merk,
                        },
                    )
                )
        return brand_ids

    brand_ids = fields.One2many(
        "cwa.product.brands.wizard",
        "wizard_id",
        string="Product Brands",
        default=_default_brand_ids,
    )

    def action_apply(self):
        self.ensure_one()
        self.brand_ids.action_apply()
        return {"type": "ir.actions.act_window_close"}


class CwaProductBrandsWizard(models.TransientModel):
    _name = "cwa.product.brands.wizard"
    _description = "CWA Product Brands Configuration"

    wizard_id = fields.Many2one(
        "cwa.product.import.brands", string="Wizard", required=True, ondelete="cascade"
    )
    cwa_product_id = fields.Many2one("cwa.product", required=True, ondelete="cascade")
    source_brand = fields.Char()
    target_brand = fields.Char(required=True)
    existing_brands = fields.Many2one("product.brand", "Select Existing Brands")

    def action_apply(self):
        for this in self:
            values = {
                "source_value": this.source_brand,
            }
            # create brand first
            if not this.existing_brands:
                brand = self.env["product.brand"].create({"name": this.target_brand})
                values["destination_value"] = brand.id
            else:
                values["destination_value"] = this.existing_brands.id
            self.env["cwa.product.brands"].create(values)
