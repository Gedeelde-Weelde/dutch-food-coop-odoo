from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_current_barcode_rule(self):
        weighted_barcode_rule = self._get_barcode_rule("weighted_barcode_rule_id")
        piece_barcode_rule = self._get_barcode_rule("piece_barcode_rule_id")

        return weighted_barcode_rule if self.is_weighted_article else piece_barcode_rule

    def _get_barcode_rule(self, rule_id):
        barcode_rule_id = self.env["ir.config_parameter"].sudo().get_param(rule_id)
        if barcode_rule_id:
            return self.env["barcode.rule"].browse(int(barcode_rule_id))
        return None
