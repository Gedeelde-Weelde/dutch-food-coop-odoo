from odoo import fields, models


class CwaUomTranslationWizard(models.TransientModel):
    _name = "cwa.uom.translation.wizard"
    _description = "UoM Translation Wizard"

    inhoud = fields.Float(
        size=64,
        required=True,
        default=lambda self: self.env.context.get("default_inhoud"),
    )
    eenheid = fields.Char(
        size=64,
        required=True,
        default=lambda self: self.env.context.get("default_eenheid"),
    )
    uom_id = fields.Many2one("uom.uom", "Standard UoM")
    uom_po_id = fields.Many2one("uom.uom", "Purchase UoM")
    target_inhoud = fields.Float()

    def action_translate_product_uom(self):
        for this in self:
            this.env["cwa.product.uom"].create(
                {
                    "inhoud": this.inhoud,
                    "eenheid": this.eenheid,
                    "uom_id": this.uom_id.id,
                    "uom_po_id": this.uom_po_id.id,
                    "target_inhoud": this.target_inhoud,
                }
            )
