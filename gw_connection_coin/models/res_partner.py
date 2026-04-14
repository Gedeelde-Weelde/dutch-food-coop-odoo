from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_cc_nummer = fields.Char(string='CC Nummer')
    x_cc_verleng = fields.Date(string='CC Verlengdatum')
    x_cc_einde = fields.Date(string='CC Einddatum')
