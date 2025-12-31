# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


# inherit this silently, to enable quantities in report as an iterable,
# and save a lot of work
class ReportProductLabelKruiden(models.AbstractModel):
    _name = "report.gw_zpl_label.label_product_product_kruiden_view"
    _inherit = "report.stock.label_product_product_view"
    _description = "Enable custom product label"
