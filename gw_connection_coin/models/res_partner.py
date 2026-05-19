from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_cc_nummer = fields.Char(string="CC Nummer")
    x_cc_verleng = fields.Date(string="CC Verlengdatum")
    x_cc_einde = fields.Date(string="CC Einddatum")
    x_automatic_debit = fields.Boolean(string="Automatische incasso")

    same_name_partner_id = fields.Many2one(
        "res.partner", string="Partner with same name", compute="_compute_duplicates"
    )
    potential_duplicate_ids = fields.Many2many(
        "res.partner",
        compute="_compute_duplicates",
        string="Potential Duplicates",
    )

    @api.depends("name", "firstname", "lastname")
    def _compute_duplicates(self):
        for partner in self:
            if not partner.name:
                partner.same_name_partner_id = False
                partner.potential_duplicate_ids = False
                continue

            # Search for partners with the same name, excluding current one
            domain = [("name", "ilike", partner.name), ("id", "!=", partner._origin.id)]
            duplicates = self.search(domain)

            partner.potential_duplicate_ids = duplicates
            partner.same_name_partner_id = duplicates[0] if duplicates else False
