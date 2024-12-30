from odoo import api, fields, models


class CwaProductImportUoMWizard(models.TransientModel):
    _name = "cwa.product.import.uom"
    _description = "Wizard for product uom/uom_po_id"

    def _default_uom_ids(self):
        # for each cwa product, determine corresponding source and target brand
        cwa_product_ids = self.env.context.get("active_ids", [])
        uom_ids = []
        uom = []
        for this in self.env["cwa.product"].browse(cwa_product_ids):
            trans = self.env["cwa.product.uom"].get_translated(this.eenheid)
            combo = this.inhoud + " " + this.eenheid
            if not trans and combo not in uom:
                uom.append(combo)
                uom_ids.append(
                    (
                        0,
                        0,
                        {
                            "cwa_product_id": this.id,
                            "eenheid": this.eenheid,
                            "inhoud": this.inhoud,
                        },
                    )
                )
        return uom_ids

    uom_ids = fields.One2many(
        "cwa.product.uom.wizard",
        "wizard_id",
        string="Product UoM",
        default=_default_uom_ids,
    )

    def action_apply(self):
        self.ensure_one()
        self.uom_ids.action_apply()
        return {"type": "ir.actions.act_window_close"}


class CwaProductImportWizard(models.TransientModel):
    _name = "cwa.product.uom.wizard"
    _description = "CWA Product UoM Configuration"

    wizard_id = fields.Many2one(
        "cwa.product.import.uom", string="Wizard", required=True, ondelete="cascade"
    )
    cwa_product_id = fields.Many2one("cwa.product", required=True, ondelete="cascade")
    inhoud = fields.Float()
    eenheid = fields.Char(required=True)
    uom_id = fields.Many2one("uom.uom", "Standard UoM", size=64)
    uom_po_id = fields.Many2one("uom.uom", "Purchase UoM", size=64)
    target_inhoud = fields.Float()

    # assume the purchase unit is same as uom, saves time!
    @api.onchange("uom_id")
    def _onchange_uom_id(self):
        if self.uom_id:
            self.uom_po_id = self.uom_id.id

    def action_apply(self):
        for this in self:
            # TODO: Also update not create only
            if this.inhoud and this.uom_id:
                values = {
                    "eenheid": this.eenheid,
                    "inhoud": this.inhoud,
                    "uom_id": this.uom_id.id,
                    "uom_po_id": this.uom_po_id.id,
                }
                self.env["cwa.product.uom"].create(values)
