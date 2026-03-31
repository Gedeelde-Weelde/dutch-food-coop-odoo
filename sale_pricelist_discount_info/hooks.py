# hooks.py
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

BATCH_SIZE = 5000


def post_init_compute_discount_total(cr, registry):
    """
    Backfill original_price, discounted_price, and discount_total
    for all existing pos.order.line records in batches,
    so the module install does not time out.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    cr.execute("SELECT COUNT(id) FROM pos_order_line WHERE discount_total IS NULL")
    total = cr.fetchone()[0]

    if not total:
        _logger.info("No pos.order.line rows to backfill — skipping.")
        return

    _logger.info(
        "Backfilling discount fields for %d pos.order.line records …", total
    )

    # --- Step 1: Set safe defaults via SQL (instant, no ORM overhead) ---
    cr.execute("""
               UPDATE pos_order_line
               SET original_price   = COALESCE(price_unit, 0),
                   discounted_price = COALESCE(price_unit, 0),
                   discount_total   = 0
               WHERE original_price IS NULL
                  OR discounted_price IS NULL
                  OR discount_total IS NULL
               """)
    _logger.info("Defaults written. Now recomputing with pricelist logic …")

    # --- Step 2: Recompute properly in batches via ORM ---
    offset = 0
    while offset < total:
        cr.execute(
            "SELECT id FROM pos_order_line ORDER BY id LIMIT %s OFFSET %s",
            (BATCH_SIZE, offset),
        )
        ids = [row[0] for row in cr.fetchall()]
        if not ids:
            break

        lines = env["pos.order.line"].browse(ids)
        for line in lines:
            line._compute_pricelist_discount_info()

        # Flush & commit each batch so we don't hold a huge transaction
        env.cr.commit()
        offset += BATCH_SIZE
        _logger.info("  … processed %d / %d", min(offset, total), total)

    _logger.info("Backfill complete.")
