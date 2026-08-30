import logging

from psycopg2 import sql

from . import models

_logger = logging.getLogger(__name__)

# Maps each manually-added (Studio) res.partner column to the module field
# that replaces it. These columns aren't owned by any module, so on a
# database where they already exist (i.e. this module is being installed
# for the first time onto a database that predates it), nothing else will
# ever populate the new fields - post_init_hook copies the values over once,
# right after install, leaving the old columns untouched.
MANUAL_CONNECTION_COIN_COLUMNS = {
    "x_cc_nummer": "cc_number",
    "x_cc_verleng": "cc_renewal_date",
    "x_cc_einde": "cc_end_date",
    "x_cc_begin": "cc_start_date",
    "x_cc_naam2": "cc_extra_holders",
}

# Kept in sync with migrations/16.0.1.2.0/pre-migrate.py's _LABELS: that
# script only runs when the module is upgraded from an earlier version, never
# on a fresh install (Odoo skips the whole migrations/ folder on install), so
# pre_init_hook below needs its own copy of the same adoption logic to avoid
# data/res_partner_category_data.xml creating duplicate categories the first
# time the module is installed onto a database that already has these tags.
CONNECTION_COIN_LABELS = [
    ("category_cc_actief", "cc actief"),
    ("category_cc_te_verlengen", "cc te verlengen"),
    ("category_cc_inactief", "cc inactief"),
]


def pre_init_hook(cr):
    # Runs before load_data(), so this must adopt the xmlids here rather
    # than in post_init_hook (which only runs after data/ has already been
    # loaded, i.e. after the duplicates would already have been created).
    for xml_id, name in CONNECTION_COIN_LABELS:
        cr.execute(
            "SELECT id FROM ir_model_data WHERE module = %s AND name = %s",
            ("gw_connection_coin", xml_id),
        )
        if cr.fetchone():
            continue

        cr.execute(
            """
            SELECT id FROM res_partner_category
            WHERE lower(name->>'nl_NL') = lower(%s)
               OR lower(name->>'en_US') = lower(%s)
            ORDER BY id
            LIMIT 1
            """,
            (name, name),
        )
        row = cr.fetchone()
        if not row:
            continue

        res_id = row[0]
        _logger.info(
            "Adopting existing res.partner.category %s ('%s') as "
            "gw_connection_coin.%s",
            res_id,
            name,
            xml_id,
        )
        cr.execute(
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            VALUES (%s, %s, 'res.partner.category', %s, FALSE)
            """,
            (xml_id, "gw_connection_coin", res_id),
        )


def post_init_hook(cr, registry):
    for old_column, new_column in MANUAL_CONNECTION_COIN_COLUMNS.items():
        cr.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'res_partner' AND column_name = %s",
            (old_column,),
        )
        if not cr.fetchone():
            continue
        _logger.info("Copying res_partner.%s into %s", old_column, new_column)
        cr.execute(
            sql.SQL(
                "UPDATE res_partner SET {new_column} = {old_column} "
                "WHERE {old_column} IS NOT NULL AND {new_column} IS NULL"
            ).format(
                new_column=sql.Identifier(new_column),
                old_column=sql.Identifier(old_column),
            )
        )
