# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_bio_basic = fields.Boolean(string='Is Bio Basic', default=False)
