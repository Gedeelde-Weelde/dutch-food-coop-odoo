import logging
import re

from odoo import _, api, fields, models
from odoo.tools import get_barcode_check_digit

from odoo.addons.queue_job.exception import RetryableJobError

from .digi_sync_base_model import DigiSyncBaseModel

_logger = logging.getLogger(__name__)


class PosCategory(DigiSyncBaseModel, models.Model):
    _inherit = "pos.category"

    external_digi_id = fields.Integer(
        string="External Digi identifier",
    )

    _sql_constraints = [
        (
            "external_digi_id",
            "unique(external_digi_id)",
            "External Digi identifier must be unique.",
        ),
    ]

    def write(self, vals):
        for record in self:
            if record.external_digi_id:
                record.send_to_digi()
        result = super().write(vals)
        return result

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if record.external_digi_id:
            record.send_to_digi()

        return record

    def send_to_digi(self):
        self.with_delay().send_to_digi_directly()

    def send_to_digi_directly(self):
        client = self._get_digi_client()
        if client:
            try:
                client.send_category_to_digi(self)
            except Exception as e:
                raise RetryableJobError(str(e), 5) from e
