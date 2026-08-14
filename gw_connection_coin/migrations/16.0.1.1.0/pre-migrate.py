import logging

# ruff: noqa
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # x_cc_vergeten is renamed to cc_forgotten (the x_ prefix and Dutch name
    # made it look like an ad-hoc user-added field, which it isn't - it's
    # owned by this module). Renaming the column here, before the ORM
    # reconciles the schema against the new field name, preserves the
    # existing forgotten-coin counts instead of Odoo dropping the old
    # column and creating an empty one.
    _logger.info("Renaming res_partner.x_cc_vergeten to cc_forgotten")
    cr.execute(
        """
        DO $$ BEGIN
        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'res_partner'
            AND column_name = 'x_cc_vergeten'
        ) THEN
            ALTER TABLE res_partner RENAME COLUMN x_cc_vergeten TO cc_forgotten;
        END IF;
        END $$;
        """
    )
