{
    "name": "Gedeelde Weelde Connection Coin",
    "version": "16.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Connection Coin for Gedeelde Weelde",
    "description": """
        Gedeelde Weelde Connection Coin module.
    """,
    "author": "Gedeelde Weelde",
    "website": "https://github.com/Gedeelde-Weelde/dutch-food-coop-odoo",
    "license": "AGPL-3",
    "depends": ["point_of_sale", "contacts", "partner_firstname"],
    "assets": {
        "point_of_sale.assets": [
            "gw_connection_coin/static/src/js/barcode_handler.js",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "wizard/connection_coin_wizard_views.xml",
        "report/connection_coin_report.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
