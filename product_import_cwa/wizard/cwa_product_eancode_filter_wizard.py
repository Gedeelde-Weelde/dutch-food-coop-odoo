from odoo import fields, models


class CwaProductEancodeFilterWizard(models.TransientModel):
    _name = "cwa.product.eancode.filter.wizard"
    _description = "Filter by Eancode"

    ean_list = fields.Text(
        string="EAN Codes", help="Enter EAN Codes separated by commas"
    )

    def apply_eancode_filter(self):
        # Parse the user's input into a list of EANs
        ean_list = [ean.strip() for ean in self.ean_list.split(",") if ean.strip()]

        # Return the filtered action
        return {
            "type": "ir.actions.act_window",
            "name": "Filtered Products",
            "res_model": "cwa.product",  # Your target model
            "view_mode": "tree,form",
            "domain": [("eancode", "in", ean_list)],
        }

    def clear_eancode_filter(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Filtered Products",
            "res_model": "cwa.product",  # Your target model
            "view_mode": "tree,form",
            "domain": [],
        }
