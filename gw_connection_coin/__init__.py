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
