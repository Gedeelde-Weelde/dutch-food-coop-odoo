{
    "name": "Sale Pricelist Discount Info",
    "version": "16.0.1.0.0",
    "category": "Sales",
    "summary": "Store original price, discounted price and total discount on sale order lines",
    "description": """
                           When a pricelist is applied to a sale order, this module records
                           the original list price, the price after pricelist discount,
                           and the total discount amount on each order line.
                       """,
    "author": "Dutch Food Coop",
    "license": "LGPL-3",
    "depends": ["sale"],
    "data": [
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
