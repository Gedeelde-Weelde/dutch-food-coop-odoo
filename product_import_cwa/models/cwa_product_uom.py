from odoo import api, fields, models


class CwaProductUom(models.Model):
    _name = "cwa.product.uom"
    _description = "Product UoM and Purchase UoM"
    _order = "eenheid"

    name = fields.Char(related="eenheid")
    inhoud = fields.Float(required=True)
    eenheid = fields.Char(size=64, required=True)
    uom_id = fields.Many2one("uom.uom", "Standard UoM", required=True)
    uom_po_id = fields.Many2one("uom.uom", "Purchase UoM", required=True)
    target_inhoud = fields.Float()

    @api.model
    def get_translated(self, source):
        return self.search([("eenheid", "=ilike", source)], limit=1)
