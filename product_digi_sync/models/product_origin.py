import logging

from odoo import api, fields, models

from odoo.addons.queue_job.exception import RetryableJobError

from .digi_sync_base_model import DigiSyncBaseModel

_logger = logging.getLogger(__name__)

EXTERNAL_DIGI_ID_START = 10000


class ProductOrigin(DigiSyncBaseModel, models.Model):
    _inherit = "product_food_fields.product_origin"

    external_digi_id = fields.Integer(
        string="External Digi identifier",
        readonly=True,
    )

    _sql_constraints = [
        (
            "external_digi_id_uniq",
            "unique(external_digi_id)",
            "External digi id must be unique.",
        ),
    ]

    @api.model
    def create(self, vals):
        records = super().create(vals)
        for record in records:
            record.external_digi_id = record.id + EXTERNAL_DIGI_ID_START
        return records

    def write(self, vals):
        result = super().write(vals)
        for record in self:
            record.send_to_digi()
        return result

    def should_send_to_digi(self):
        return self.external_digi_id is not None

    def send_to_digi_directly(self):
        client = self._get_digi_client()
        if client:
            try:
                client.send_product_origin_to_digi(self)
            except Exception as e:
                raise RetryableJobError(str(e), 5) from e
