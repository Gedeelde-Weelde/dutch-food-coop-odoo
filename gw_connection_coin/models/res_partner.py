import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Lead time and grace period for the reminder/auto-end crons below.
    CONNECTION_COIN_REMINDER_LEAD_DAYS = 28
    CONNECTION_COIN_AUTO_END_GRACE_MONTHS = 2
    CONNECTION_COIN_NUMMER_MAX_DIGITS = 5
    # Fields that drive both the validation constraints and the status
    # label below - x_cc_begin/x_is_ondernemerslid are deliberately not
    # declared in this module (see the comment above _compute_is_member),
    # so both are handled defensively wherever they're read.
    CONNECTION_COIN_STATUS_FIELDS = (
        "x_cc_nummer",
        "x_cc_verleng",
        "x_cc_einde",
        "x_cc_begin",
    )
    CONNECTION_COIN_STATUS_CATEGORY_XMLIDS = {
        "actief": "gw_connection_coin.category_cc_actief",
        "te_verlengen": "gw_connection_coin.category_cc_te_verlengen",
        "inactief": "gw_connection_coin.category_cc_inactief",
    }

    x_cc_nummer = fields.Char(string="CC Nummer")
    x_cc_verleng = fields.Date(string="CC Verlengdatum")
    x_cc_einde = fields.Date(string="CC Einddatum")
    x_automatic_debit = fields.Boolean(string="Automatische incasso")
    cc_forgotten = fields.Integer(string="CC Keer Vergeten", default=0)
    cc_reminder_sent_date = fields.Date(string="CC Herinnering Verzonden")
    is_member = fields.Boolean(compute="_compute_is_member")

    @api.model
    def _cc_nummer_to_barcode(self, cc_nummer):
        try:
            nummer = int(cc_nummer)
        except (ValueError, TypeError):
            raise ValidationError(
                _("Connection Coin: 'CC Nummer' %s moet een getal zijn.") % cc_nummer
            ) from None
        if not 0 <= nummer < 10**self.CONNECTION_COIN_NUMMER_MAX_DIGITS:
            raise ValidationError(
                _(
                    "Connection Coin nummer %s is ongeldig: mag maximaal uit "
                    "%s cijfers bestaan."
                )
                % (cc_nummer, self.CONNECTION_COIN_NUMMER_MAX_DIGITS)
            )
        return "042" + str(nummer).zfill(self.CONNECTION_COIN_NUMMER_MAX_DIGITS)

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
        partners = super().create(vals_list)
        partners._update_connection_coin_labels()
        return partners

    def end_connection_coin(self):
        for partner in self:
            partner.write(
                {
                    "x_cc_einde": partner.x_cc_verleng,
                    "x_cc_verleng": False,
                    "cc_reminder_sent_date": False,
                }
            )

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

    @api.constrains("x_cc_verleng", "x_is_ondernemerslid")
    def _check_connection_coin_ondernemerslid(self):
        if "x_is_ondernemerslid" not in self._fields:
            return
        for partner in self:
            if partner.x_is_ondernemerslid and partner.x_cc_verleng:
                raise ValidationError(
                    _(
                        "Connection Coin: %s is ondernemerslid, dan mag er "
                        "geen 'CC Verlengdatum' ingevuld staan."
                    )
                    % partner.display_name
                )

    @api.constrains(*CONNECTION_COIN_STATUS_FIELDS, "x_is_ondernemerslid")
    def _check_connection_coin_consistency(self):
        has_begin = "x_cc_begin" in self._fields
        has_ondernemerslid = "x_is_ondernemerslid" in self._fields
        for partner in self:
            heeft_nummer = bool(partner.x_cc_nummer)
            begin = partner.x_cc_begin if has_begin else False
            is_ondernemerslid = (
                partner.x_is_ondernemerslid if has_ondernemerslid else False
            )

            if partner.x_cc_einde:
                if has_begin and not begin:
                    raise ValidationError(
                        _(
                            "Connection Coin: er staat een 'CC Einddatum' bij "
                            "%s, maar geen 'CC Begindatum'."
                        )
                        % partner.display_name
                    )
                if not heeft_nummer:
                    raise ValidationError(
                        _(
                            "Connection Coin: er staat een 'CC Einddatum' bij "
                            "%s, maar geen 'CC Nummer'."
                        )
                        % partner.display_name
                    )
                if partner.x_cc_verleng:
                    raise ValidationError(
                        _(
                            "Connection Coin: %s heeft een 'CC Einddatum', "
                            "dan mag er geen 'CC Verlengdatum' meer ingevuld "
                            "staan."
                        )
                        % partner.display_name
                    )

            if partner.x_cc_verleng:
                if has_begin and not begin:
                    raise ValidationError(
                        _(
                            "Connection Coin: er staat een 'CC Verlengdatum' "
                            "bij %s, maar geen 'CC Begindatum'."
                        )
                        % partner.display_name
                    )
                if not heeft_nummer:
                    raise ValidationError(
                        _(
                            "Connection Coin: er staat een 'CC Verlengdatum' "
                            "bij %s, maar geen 'CC Nummer'."
                        )
                        % partner.display_name
                    )

            if has_begin and begin and not heeft_nummer:
                raise ValidationError(
                    _(
                        "Connection Coin: er staat een 'CC Begindatum' bij "
                        "%s, maar geen 'CC Nummer'."
                    )
                    % partner.display_name
                )

            if not heeft_nummer:
                continue

            if has_begin and not begin:
                raise ValidationError(
                    _(
                        "Connection Coin: 'CC Begindatum' is verplicht zodra "
                        "er een 'CC Nummer' is ingevuld bij %s."
                    )
                    % partner.display_name
                )
            if (
                not partner.x_cc_verleng
                and not partner.x_cc_einde
                and not is_ondernemerslid
            ):
                raise ValidationError(
                    _(
                        "Connection Coin: 'CC Verlengdatum' of 'CC Einddatum' "
                        "is verplicht voor %s (behalve voor ondernemersleden)."
                    )
                    % partner.display_name
                )
            if has_begin and begin:
                if partner.x_cc_verleng and partner.x_cc_verleng < begin:
                    raise ValidationError(
                        _(
                            "Connection Coin: 'CC Verlengdatum' mag niet "
                            "vóór 'CC Begindatum' liggen bij %s."
                        )
                        % partner.display_name
                    )
                if partner.x_cc_einde and partner.x_cc_einde < begin:
                    raise ValidationError(
                        _(
                            "Connection Coin: 'CC Einddatum' mag niet vóór "
                            "'CC Begindatum' liggen bij %s."
                        )
                        % partner.display_name
                    )

    def _compute_connection_coin_status(self):
        self.ensure_one()
        if not self.x_cc_nummer:
            return None
        today = fields.Date.context_today(self)
        if "x_cc_begin" in self._fields and self.x_cc_begin and self.x_cc_begin > today:
            # Coin not yet active: none of the three status labels apply.
            return None
        if self.x_cc_einde and self.x_cc_einde <= today:
            return "inactief"
        if self.x_cc_verleng and self.x_cc_verleng < today:
            return "te_verlengen"
        return "actief"

    def _update_connection_coin_labels(self):
        categories = {
            key: self.env.ref(xmlid, raise_if_not_found=False)
            for key, xmlid in self.CONNECTION_COIN_STATUS_CATEGORY_XMLIDS.items()
        }
        all_category_ids = {category.id for category in categories.values() if category}
        for partner in self:
            target = categories.get(partner._compute_connection_coin_status())
            current_ids = set(partner.category_id.ids) & all_category_ids
            target_ids = {target.id} if target else set()
            if current_ids == target_ids:
                continue
            commands = [(3, cat_id) for cat_id in current_ids - target_ids]
            commands += [(4, cat_id) for cat_id in target_ids - current_ids]
            partner.write({"category_id": commands})

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
            # x_cc_verleng and x_cc_einde are mutually exclusive
            # (_check_connection_coin_consistency), so any partner matched
            # by the domain above never has an x_cc_einde to check.
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
        update_labels = any(
            fname in vals for fname in self.CONNECTION_COIN_STATUS_FIELDS
        )
        result = super().write(vals)
        if update_labels:
            self._update_connection_coin_labels()
        return result

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
