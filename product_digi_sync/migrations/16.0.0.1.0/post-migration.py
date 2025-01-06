import logging

# ruff: noqa
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Removing sql constraint shop_plucode_uniq")
    # Safely drop the SQL constraint if it exists
    cr.execute(
        """
           DO $$ BEGIN
           IF EXISTS (
               SELECT 1
               FROM information_schema.table_constraints
               WHERE constraint_name = 'product_template_shop_plucode_uniq'
               AND table_name = 'product_template'
           ) THEN
               ALTER TABLE product_template DROP CONSTRAINT product_template_shop_plucode_uniq;
           END IF;
           END $$;
       """
    )
