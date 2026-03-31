{
    "name": "POS Pricelist Discount Info",
    "version": "16.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Store original price, discounted price and total discount on POS order lines",
    "description": """
                           When a pricelist is applied to a POS order, this module records
                           the original list price, the price after pricelist discount,
                           and the total discount amount on each order line.
                       """,
    "author": "Dutch Food Coop",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "views/pos_order_views.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "sale_pricelist_discount_info/static/src/js/models.js",
        ],
    },
    "post_init_hook": "post_init_compute_discount_total",
    "installable": True,
    "application": False,
    "auto_install": False,
}
