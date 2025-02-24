from unittest.mock import Mock, patch

from odoo.addons.base.models.ir_config_parameter import IrConfigParameter
from odoo.addons.product_digi_sync.models.digi_client import DigiClient
from odoo.addons.queue_job.models.base import Base as QueueJobBase

from .digi_sync_base_test_case import DigiSyncBaseTestCase


class PosCategoryTestCase(DigiSyncBaseTestCase):
    def setUp(self):
        super().setUp()

        def mock_with_delay(with_delay_self):
            return with_delay_self

        self.patcher = patch.object(QueueJobBase, "with_delay", mock_with_delay)
        self.patcher.start()

    def tearDown(self):
        super().tearDown()
        self.patcher.stop()

    def test_it_doesnt_send_the_category_to_digi_after_save_when_external_id_not_set(
        self
    ):
        digi_client = self.env["product_digi_sync.digi_client"].create(
            {
                "name": "Test Digi Client",
                "username": "user",
                "password": "<PASSWORD>",
            }
        )

        patch.object(IrConfigParameter, "get_param", digi_client.id)

        with patch.object(
            DigiClient, "send_category_to_digi"
        ) as mock_send_category_to_digi:
            category = self.env["pos.category"].create(
                {
                    "name": "Test Category",
                }
            )
            category.write(
                {
                    "name": "Test Category altered",
                }
            )

            self.assertEqual(mock_send_category_to_digi.call_count, 0)

    def test_is_sends_the_category_to_digi_when_external_id_is_set(self):
        digi_client = self.env["product_digi_sync.digi_client"].create(
            {
                "name": "Test Digi Client",
                "username": "user",
                "password": "<PASSWORD>",
            }
        )

        client_id = digi_client.id
        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "digi_client_id", client_id
        )
        patched_get_param.start()
        send_category_to_digi = Mock()
        mock_send_category_to_digi = patch.object(
            DigiClient, "send_category_to_digi", send_category_to_digi
        ).start()
        category = self.env["pos.category"].create(
            {
                "name": "Test Category",
                "external_digi_id": 1145,
            }
        )
        category.write(
            {
                "name": "Test Category altered",
            }
        )

        self.assertEqual(mock_send_category_to_digi.call_args[0][0], category)
        patched_get_param.stop()
