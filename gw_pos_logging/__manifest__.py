# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "POS Order Logging",
    "version": "16.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Logs POS order operations and payment events to browser database",
    "author": "Gedeelde Weelde",
    "website": "https://github.com/Gedeelde-Weelde/dutch-food-coop-odoo",
    "license": "AGPL-3",
    "depends": ["point_of_sale"],
    "data": [],
    "assets": {
        "point_of_sale.assets": [
            "gw_pos_logging/static/src/js/pos_payment_logging.js",
            "gw_pos_logging/static/src/js/pos_order_logging.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
