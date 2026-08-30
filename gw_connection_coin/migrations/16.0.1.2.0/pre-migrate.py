import logging

# ruff: noqa
_logger = logging.getLogger(__name__)

# (xml_id, name) - name is matched case-insensitively against either
# translation of the existing res.partner.category, since these tags were
# created by hand and their name is the only reliable anchor available.
_LABELS = [
    ("category_cc_actief", "cc actief"),
    ("category_cc_te_verlengen", "cc te verlengen"),
    ("category_cc_inactief", "cc inactief"),
]


def migrate(cr, version):
    # Bind these xmlids onto the res.partner.category rows that were
    # created manually in production for the connection-coin status
    # labels, before data/res_partner_category_data.xml loads. Odoo then
    # updates those existing rows in place instead of creating duplicates,
    # so every partner already tagged with them keeps that tag.
    for xml_id, name in _LABELS:
        cr.execute(
            "SELECT id FROM ir_model_data WHERE module = %s AND name = %s",
            ("gw_connection_coin", xml_id),
        )
        if cr.fetchone():
            _logger.info("gw_connection_coin.%s is already bound, skipping.", xml_id)
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
            _logger.info(
                "No existing '%s' res.partner.category found, "
                "data/res_partner_category_data.xml will create it fresh.",
                name,
            )
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
