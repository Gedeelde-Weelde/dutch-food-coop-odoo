import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Lead time and grace period for the reminder/auto-end crons below.
    CONNECTION_COIN_REMINDER_LEAD_DAYS = 28
    CONNECTION_COIN_AUTO_END_GRACE_MONTHS = 2

    x_cc_nummer = fields.Char(string="CC Nummer")
    x_cc_verleng = fields.Date(string="CC Verlengdatum")
    x_cc_einde = fields.Date(string="CC Einddatum")
    x_automatic_debit = fields.Boolean(string="Automatische incasso")
    cc_forgotten = fields.Integer(string="CC Keer Vergeten", default=0)
    cc_reminder_sent_date = fields.Date(string="CC Herinnering Verzonden")
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
        result = {}
        for partner in self:
            vals = {
                "x_cc_einde": partner.x_cc_verleng,
                "x_cc_verleng": False,
                "cc_reminder_sent_date": False,
            }
            partner.write(vals)
            result[partner.id] = vals
        return result

    def extend_connection_coin(self):
        today = fields.Date.context_today(self)
        for partner in self:
            vals = {"cc_forgotten": 0, "cc_reminder_sent_date": False}
            if partner.x_cc_einde and partner.x_cc_einde < today:
                vals["x_cc_verleng"] = today + relativedelta(years=1)
                vals["x_cc_einde"] = False
            elif partner.x_cc_verleng:
                vals["x_cc_verleng"] = partner.x_cc_verleng + relativedelta(years=1)
            partner.write(vals)

    def mark_connection_coin_forgotten(self):
        self.ensure_one()
        self.cc_forgotten += 1
        return self.cc_forgotten

    @api.model
    def _cron_send_connection_coin_reminders(self):
        today = fields.Date.context_today(self)
        target_date = today + relativedelta(
            days=self.CONNECTION_COIN_REMINDER_LEAD_DAYS
        )
        template = self.env.ref(
            "gw_connection_coin.mail_template_connection_coin_reminder"
        )
        partners = self.search(
            [
                ("x_cc_verleng", "!=", False),
                ("x_cc_verleng", ">=", today),
                ("x_cc_verleng", "<=", target_date),
                ("cc_reminder_sent_date", "=", False),
            ]
        )
        for partner in partners:
            if partner.x_cc_einde and partner.x_cc_einde <= partner.x_cc_verleng:
                continue
            try:
                template.send_mail(partner.id)
            except Exception:
                _logger.exception(
                    "Failed to send connection coin reminder to partner %s",
                    partner.id,
                )
                continue
            partner.cc_reminder_sent_date = today

    @api.model
    def _cron_end_overdue_connection_coins(self):
        today = fields.Date.context_today(self)
        threshold = today - relativedelta(
            months=self.CONNECTION_COIN_AUTO_END_GRACE_MONTHS
        )
        template = self.env.ref("gw_connection_coin.mail_template_connection_coin_ended")
        partners = self.search(
            [
                ("x_cc_verleng", "!=", False),
                ("x_cc_verleng", "<=", threshold),
                ("x_cc_einde", "=", False),
            ]
        )
        for partner in partners:
            partner.end_connection_coin()
            try:
                template.send_mail(partner.id)
            except Exception:
                _logger.exception(
                    "Failed to send connection coin termination email to partner %s",
                    partner.id,
                )

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
