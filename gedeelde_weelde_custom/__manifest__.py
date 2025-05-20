# -*- coding: utf-8 -*-
{
    'name': "gedeelde_weelde_custom",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

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
        "product",
        "product_import_cwa",
        "point_of_sale",
        "sale",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
    ],

}
