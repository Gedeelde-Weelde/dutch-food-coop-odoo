# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProductLabelLayout(models.TransientModel):
    _inherit = "product.label.layout"

    # add only the new selection value
    print_format = fields.Selection(
        selection_add=[
            ("zpl_custom", "Custom ZPL label"),
        ],
        ondelete={
            "zpl_custom": "set default",
        },
    )

    custom_zpl_report_id = fields.Many2one(
        "ir.actions.report",
        domain=[("model", "=", "product.product"), ("report_type", "=", "qweb-text")],
        help="Choose ZPL label layout",
    )

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()
        if self.print_format == "zpl_custom" and self.custom_zpl_report_id:
            external_ids = self.custom_zpl_report_id.get_external_id()
            chosen_xmlid = external_ids.get(self.custom_zpl_report_id.id)
            if chosen_xmlid:
                xml_id = chosen_xmlid
        return xml_id, data
