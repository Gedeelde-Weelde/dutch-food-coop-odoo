{
    "name": "product_digi_sync",
    "summary": """
        Allows for syncing products to Digi using the @Fresh api""",
    "author": "Gedeelde Weelde",
    "license": "AGPL-3",
    "website": "https://github.com/Gedeelde-Weelde/dutch-food-coop-odoo",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Sales/Point of Sale",
    "version": "16.0.0.1.0",
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/pos_category_views.xml",
        "views/product_origin_views.xml",
        "views/product_quality_views.xml",
        "views/digi_client_views.xml",
        "views/digi_client_settings_view.xml",
        "views/barcode_rule.views.xml",
    ],
    # any module necessary for this one to work correctly
    "depends": [
        "product_food_fields",
        "product",
        "point_of_sale",
        "queue_job",
        "sale",
        "product_brand",
        "product_import_cwa",
    ],
    "installable": True,
}
