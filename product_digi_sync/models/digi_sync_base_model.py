import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DigiSyncBaseModel(models.AbstractModel):
    _name = "product_digi_sync.digi_sync_base"
    _description = "Base class for Digi Sync models"

    def send_to_digi(self):
        self.ensure_one()
        if self.should_send_to_digi():
            self.with_delay().send_to_digi_directly()

    def send_to_digi_directly(self):
        pass

    def should_send_to_digi(self):
        return True

    def _get_digi_client(self):
        digi_client_id = int(
            self.env["ir.config_parameter"].sudo().get_param("digi_client_id")
        )
        client = self.env["product_digi_sync.digi_client"].browse(digi_client_id)
        if not client.exists():
            _logger.warning("Digi client requested, but no client was configured.")
            return False
        return client
