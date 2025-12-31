# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "GW ZPL Label",
    "version": "16.0.1.0.0",
    "summary": "Custom ZPL label layout for Kruiden",
    "author": "Therp BV, Gedeelde Weelde",
    "website": "https://github.com/Gedeelde-Weelde/dutch-food-coop-odoo",
    "license": "AGPL-3",
    "depends": [
        "product",
        "stock",
    ],
    "data": [
        "report/kruiden_label_templates.xml",
        "wizard/product_label_layout_views.xml",
    ],
    "installable": True,
    "application": False,
}
