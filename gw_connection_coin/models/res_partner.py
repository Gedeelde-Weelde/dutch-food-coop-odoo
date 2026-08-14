from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_cc_nummer = fields.Char(string="CC Nummer")
    x_cc_verleng = fields.Date(string="CC Verlengdatum")
    x_cc_einde = fields.Date(string="CC Einddatum")
    x_automatic_debit = fields.Boolean(string="Automatische incasso")
    x_cc_vergeten = fields.Integer(string="CC Keer Vergeten", default=0)
    is_member = fields.Boolean(compute="_compute_is_member")

    @api.model
    def _cc_nummer_to_barcode(self, cc_nummer):
        return "042" + str(int(cc_nummer)).zfill(5)

    @api.onchange("x_cc_nummer")
    def _onchange_x_cc_nummer(self):
        self.barcode = (
            self._cc_nummer_to_barcode(self.x_cc_nummer) if self.x_cc_nummer else False
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("x_cc_nummer"):
                vals["barcode"] = self._cc_nummer_to_barcode(vals["x_cc_nummer"])
        return super().create(vals_list)

    def end_connection_coin(self):
        for partner in self:
            partner.x_cc_einde = partner.x_cc_verleng

    def extend_connection_coin(self):
        for partner in self:
            if partner.x_cc_verleng:
                partner.x_cc_verleng = partner.x_cc_verleng + relativedelta(years=1)

    def mark_connection_coin_forgotten(self):
        self.ensure_one()
        self.x_cc_vergeten += 1
        return self.x_cc_vergeten

    # x_lid_begin/x_lid_einde are pre-existing manual fields (added directly
    # in the database long before this module existed), deliberately not
    # declared here: declaring a field with the same name in code would make
    # Odoo adopt it as owned by this module, and it would then get dropped
    # (column and data) if the module is ever uninstalled. Since they're
    # manual fields, they're already available as normal attributes at
    # runtime on databases that have them - just not on a fresh install/CI
    # database, so this is deliberately not in @api.depends (which would
    # fail model setup entirely if the fields don't exist) and instead
    # checked defensively at compute time.
    @api.depends()
    def _compute_is_member(self):
        today = fields.Date.context_today(self)
        has_membership_fields = "x_lid_begin" in self._fields
        for partner in self:
            if not has_membership_fields or not partner.x_lid_begin:
                partner.is_member = False
                continue
            partner.is_member = partner.x_lid_begin <= today and (
                not partner.x_lid_einde or today <= partner.x_lid_einde
            )

    def write(self, vals):
        if "x_cc_nummer" in vals:
            vals["barcode"] = (
                self._cc_nummer_to_barcode(vals["x_cc_nummer"])
                if vals["x_cc_nummer"]
                else False
            )
        return super().write(vals)

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
