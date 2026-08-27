from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase

MAIL_TEMPLATE_SEND_MAIL = "odoo.addons.mail.models.mail_template.MailTemplate.send_mail"
# cc_start_date is now a required companion of cc_number (see
# _check_connection_coin_consistency), so tests that don't specifically
# exercise begin-date ordering just need any date safely before every other
# date used below.
DEFAULT_CC_START_DATE = fields.Date.from_string("2020-01-01")


class TestResPartner(TransactionCase):
    def test_barcode_set_from_cc_nummer(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
            }
        )
        self.assertEqual(partner.barcode, "04200711")

    def test_barcode_set_from_cc_nummer_on_write(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        partner.write(
            {
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
            }
        )
        self.assertEqual(partner.barcode, "04200711")

    def test_barcode_cleared_when_cc_nummer_removed(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
            }
        )
        partner.write(
            {"cc_number": False, "cc_start_date": False, "cc_renewal_date": False}
        )
        self.assertEqual(partner.barcode, False)

    def test_end_connection_coin_sets_einde_to_verleng(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
            }
        )
        partner.end_connection_coin()
        self.assertEqual(partner.cc_end_date, fields.Date.from_string("2026-01-01"))

    def test_end_connection_coin_clears_verleng(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
            }
        )
        partner.end_connection_coin()
        self.assertEqual(partner.cc_renewal_date, False)

    def test_end_connection_coin_returns_new_state_per_partner(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
                "cc_reminder_sent_date": fields.Date.today(),
            }
        )
        result = partner.end_connection_coin()
        self.assertEqual(
            result[partner.id],
            {
                "cc_end_date": fields.Date.from_string("2026-01-01"),
                "cc_renewal_date": False,
                "cc_reminder_sent_date": False,
            },
        )

    def test_end_connection_coin_clears_reminder_sent_date(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
                "cc_reminder_sent_date": fields.Date.today(),
            }
        )
        partner.end_connection_coin()
        self.assertEqual(partner.cc_reminder_sent_date, False)

    def test_extend_connection_coin_advances_verleng_by_one_year(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
            }
        )
        partner.extend_connection_coin()
        self.assertEqual(partner.cc_renewal_date, fields.Date.from_string("2027-01-01"))

    def test_extend_connection_coin_noop_without_verleng(self):
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        partner.extend_connection_coin()
        self.assertEqual(partner.cc_renewal_date, False)

    def test_extend_connection_coin_sets_verleng_when_einde_in_past(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_end_date": fields.Date.today() - relativedelta(days=1),
            }
        )
        partner.extend_connection_coin()
        self.assertEqual(
            partner.cc_renewal_date, fields.Date.today() + relativedelta(years=1)
        )
        self.assertEqual(partner.cc_end_date, False)

    def test_extend_connection_coin_clears_reminder_sent_date(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
                "cc_reminder_sent_date": fields.Date.today(),
            }
        )
        partner.extend_connection_coin()
        self.assertEqual(partner.cc_reminder_sent_date, False)

    def test_extend_connection_coin_resets_forgotten_count(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.from_string("2026-01-01"),
            }
        )
        partner.mark_connection_coin_forgotten()
        partner.mark_connection_coin_forgotten()
        self.assertEqual(partner.cc_forgotten, 2)
        partner.extend_connection_coin()
        self.assertEqual(partner.cc_forgotten, 0)

    def test_mark_connection_coin_forgotten_increments_count(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
            }
        )
        self.assertEqual(partner.cc_forgotten, 0)
        result = partner.mark_connection_coin_forgotten()
        self.assertEqual(partner.cc_forgotten, 1)
        self.assertEqual(result, 1)
        partner.mark_connection_coin_forgotten()
        self.assertEqual(partner.cc_forgotten, 2)

    def test_is_member_false_when_membership_fields_absent(self):
        # On a database without the manually-added x_lid_begin/x_lid_einde
        # fields (e.g. this test database), is_member must degrade to False
        # instead of raising.
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.assertFalse(partner.is_member)


class TestResPartnerMembership(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Simulate the pre-existing manual (Studio-added) x_lid_begin/
        # x_lid_einde fields that _compute_is_member reads defensively,
        # without gw_connection_coin declaring them in code (see the
        # comment above _compute_is_member for why).
        model_id = cls.env["ir.model"]._get_id("res.partner")
        cls.env["ir.model.fields"].create(
            [
                {
                    "name": "x_lid_begin",
                    "field_description": "Lidmaatschap Startdatum",
                    "model_id": model_id,
                    "ttype": "date",
                },
                {
                    "name": "x_lid_einde",
                    "field_description": "Lidmaatschap Einddatum",
                    "model_id": model_id,
                    "ttype": "date",
                },
            ]
        )

    def test_is_member_true_within_range(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_lid_begin": fields.Date.today() - relativedelta(days=1),
                "x_lid_einde": fields.Date.today() + relativedelta(days=1),
            }
        )
        self.assertTrue(partner.is_member)

    def test_is_member_true_without_end_date(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_lid_begin": fields.Date.today() - relativedelta(days=1),
            }
        )
        self.assertTrue(partner.is_member)

    def test_is_member_false_before_begin(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_lid_begin": fields.Date.today() + relativedelta(days=1),
            }
        )
        self.assertFalse(partner.is_member)

    def test_is_member_false_after_end(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "x_lid_begin": fields.Date.today() - relativedelta(days=10),
                "x_lid_einde": fields.Date.today() - relativedelta(days=1),
            }
        )
        self.assertFalse(partner.is_member)

    def test_is_member_false_without_begin_date(self):
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.assertFalse(partner.is_member)


class TestResPartnerConnectionCoinCron(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {"name": "Test Partner", "email": "test@example.com"}
        )

    def test_reminder_cron_sends_mail_within_lead_time(self):
        today = fields.Date.today()
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": today + relativedelta(days=10),
            }
        )
        with patch(MAIL_TEMPLATE_SEND_MAIL) as send_mail:
            self.env["res.partner"]._cron_send_connection_coin_reminders()
        send_mail.assert_called_once_with(self.partner.id)
        self.assertEqual(self.partner.cc_reminder_sent_date, today)

    def test_reminder_cron_skips_partner_already_reminded(self):
        today = fields.Date.today()
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": today + relativedelta(days=10),
                "cc_reminder_sent_date": today,
            }
        )
        with patch(MAIL_TEMPLATE_SEND_MAIL) as send_mail:
            self.env["res.partner"]._cron_send_connection_coin_reminders()
        send_mail.assert_not_called()

    def test_reminder_cron_skips_partner_outside_lead_time(self):
        today = fields.Date.today()
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": today + relativedelta(days=40),
            }
        )
        with patch(MAIL_TEMPLATE_SEND_MAIL) as send_mail:
            self.env["res.partner"]._cron_send_connection_coin_reminders()
        send_mail.assert_not_called()

    def test_reminder_cron_recovers_from_missed_run(self):
        # A partner whose verleng date was already within the lead time
        # yesterday (e.g. the cron didn't run) must still be picked up
        # today, unlike the original exact-date-match implementation.
        today = fields.Date.today()
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": today + relativedelta(days=1),
            }
        )
        with patch(MAIL_TEMPLATE_SEND_MAIL) as send_mail:
            self.env["res.partner"]._cron_send_connection_coin_reminders()
        send_mail.assert_called_once_with(self.partner.id)

    def test_auto_end_cron_ends_overdue_coin_and_sends_mail(self):
        today = fields.Date.today()
        overdue_verleng = today - relativedelta(months=3)
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": overdue_verleng,
            }
        )
        with patch(MAIL_TEMPLATE_SEND_MAIL) as send_mail:
            self.env["res.partner"]._cron_end_overdue_connection_coins()
        self.assertEqual(self.partner.cc_end_date, overdue_verleng)
        self.assertEqual(self.partner.cc_renewal_date, False)
        send_mail.assert_called_once_with(self.partner.id)

    def test_auto_end_cron_ignores_recent_verleng(self):
        today = fields.Date.today()
        recent_verleng = today - relativedelta(days=10)
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": recent_verleng,
            }
        )
        with patch(MAIL_TEMPLATE_SEND_MAIL) as send_mail:
            self.env["res.partner"]._cron_end_overdue_connection_coins()
        send_mail.assert_not_called()
        self.assertEqual(self.partner.cc_renewal_date, recent_verleng)

    def test_auto_end_cron_ignores_already_ended_coin(self):
        today = fields.Date.today()
        self.partner.write(
            {
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": False,
                "cc_end_date": today - relativedelta(months=3),
            }
        )
        with patch(MAIL_TEMPLATE_SEND_MAIL) as send_mail:
            self.env["res.partner"]._cron_end_overdue_connection_coins()
        send_mail.assert_not_called()


class TestResPartnerConnectionCoinValidation(TransactionCase):
    def test_non_numeric_cc_nummer_raises(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {"name": "Test Partner", "cc_number": "ABC"}
            )

    def test_cc_nummer_too_long_raises(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {"name": "Test Partner", "cc_number": "123456"}
            )

    def test_cc_end_date_requires_nummer(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {"name": "Test Partner", "cc_end_date": fields.Date.today()}
            )

    def test_cc_renewal_date_requires_nummer(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {"name": "Test Partner", "cc_renewal_date": fields.Date.today()}
            )

    def test_cc_number_requires_verleng_or_einde(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {
                    "name": "Test Partner",
                    "cc_number": "711",
                    "cc_start_date": DEFAULT_CC_START_DATE,
                }
            )

    def test_cc_end_date_and_verleng_mutually_exclusive(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
            }
        )
        with self.assertRaises(ValidationError):
            partner.write({"cc_end_date": fields.Date.today()})

    def test_valid_connection_coin_data_does_not_raise(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
            }
        )
        self.assertTrue(partner)

    def test_verleng_requires_begin(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {
                    "name": "Test Partner",
                    "cc_number": "711",
                    "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
                }
            )

    def test_begin_requires_nummer(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {"name": "Test Partner", "cc_start_date": fields.Date.today()}
            )

    def test_verleng_before_begin_raises(self):
        begin = fields.Date.today()
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {
                    "name": "Test Partner",
                    "cc_number": "711",
                    "cc_start_date": begin,
                    "cc_renewal_date": begin - relativedelta(days=1),
                }
            )

    def test_einde_before_begin_raises(self):
        begin = fields.Date.today()
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {
                    "name": "Test Partner",
                    "cc_number": "711",
                    "cc_start_date": begin,
                    "cc_end_date": begin - relativedelta(days=1),
                }
            )

    def test_not_yet_started_gets_no_label(self):
        actief = self.env.ref("gw_connection_coin.category_cc_actief")
        te_verlengen = self.env.ref("gw_connection_coin.category_cc_te_verlengen")
        inactief = self.env.ref("gw_connection_coin.category_cc_inactief")
        future_begin = fields.Date.today() + relativedelta(days=5)
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": future_begin,
                "cc_renewal_date": future_begin + relativedelta(days=1),
            }
        )
        self.assertFalse(partner.category_id & (actief | te_verlengen | inactief))


class TestResPartnerConnectionCoinLabels(TransactionCase):
    def setUp(self):
        super().setUp()
        self.actief = self.env.ref("gw_connection_coin.category_cc_actief")
        self.te_verlengen = self.env.ref("gw_connection_coin.category_cc_te_verlengen")
        self.inactief = self.env.ref("gw_connection_coin.category_cc_inactief")
        self.status_categories = self.actief | self.te_verlengen | self.inactief

    def _label(self, partner):
        return partner.category_id & self.status_categories

    def test_active_coin_gets_actief_label(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
            }
        )
        self.assertEqual(self._label(partner), self.actief)

    def test_overdue_verleng_gets_te_verlengen_label(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() - relativedelta(days=1),
            }
        )
        self.assertEqual(self._label(partner), self.te_verlengen)

    def test_ended_coin_gets_inactief_label(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_end_date": fields.Date.today(),
            }
        )
        self.assertEqual(self._label(partner), self.inactief)

    def test_no_nummer_gets_no_label(self):
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.assertFalse(self._label(partner))

    def test_label_removed_when_nummer_cleared(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
            }
        )
        self.assertEqual(self._label(partner), self.actief)
        partner.write(
            {"cc_number": False, "cc_start_date": False, "cc_renewal_date": False}
        )
        self.assertFalse(self._label(partner))

    def test_label_updates_on_extend_connection_coin(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() - relativedelta(days=1),
            }
        )
        self.assertEqual(self._label(partner), self.te_verlengen)
        partner.extend_connection_coin()
        self.assertEqual(self._label(partner), self.actief)

    def test_label_updates_on_end_connection_coin(self):
        # end_connection_coin copies cc_renewal_date into cc_end_date as-is, so
        # starting from an overdue (past) verleng is what actually yields a
        # past einde - and thus an immediate "inactief" status below.
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() - relativedelta(days=1),
            }
        )
        self.assertEqual(self._label(partner), self.te_verlengen)
        partner.end_connection_coin()
        self.assertEqual(self._label(partner), self.inactief)

    def test_existing_unrelated_labels_preserved(self):
        other_tag = self.env["res.partner.category"].create({"name": "Other Tag"})
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "cc_number": "711",
                "cc_start_date": DEFAULT_CC_START_DATE,
                "cc_renewal_date": fields.Date.today() + relativedelta(days=10),
                "category_id": [(4, other_tag.id)],
            }
        )
        self.assertIn(other_tag, partner.category_id)
        self.assertEqual(self._label(partner), self.actief)
