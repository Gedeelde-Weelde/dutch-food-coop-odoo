{
    "name": "gedeelde_weelde_custom",
    "summary": """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    "author": "Gedeelde Weelde",
    "license": "AGPL-3",
    "website": "https://github.com/Gedeelde-Weelde/dutch-food-coop-odoo",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Sales/Point of Sale",
    "version": "16.0.0.0.1",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "barcodes",
        "product",
        "product_import_cwa",
        "point_of_sale",
        "sale",
    ],
    "assets": {
        "point_of_sale.assets": [
            "gedeelde_weelde_custom/static/src/js/extend_barcode_parser.js",
            "gedeelde_weelde_custom/static/src/js/extend_products_screen_barcode.js",
            "gedeelde_weelde_custom/static/src/js/extend_payment_screen.js",
            "gedeelde_weelde_custom/static/src/js/extend_products_screen_discount.js",
            "gedeelde_weelde_custom/static/src/js/focus_warning_pos_component.js",
            "gedeelde_weelde_custom/static/src/js/pos_order_receipt.js",
            "gedeelde_weelde_custom/static/src/xml/receipt_screen.xml",
            "gedeelde_weelde_custom/static/src/xml/mouse_leave_overlay.xml",
            "gedeelde_weelde_custom/static/src/xml/order_receipt.xml",
            "gedeelde_weelde_custom/static/src/xml/customer_facing_display_order_line_template.xml",
            "gedeelde_weelde_custom/static/src/css/pos_custom.scss",
        ],
    },
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/barcode_rule_views.xml",
    ],
}
