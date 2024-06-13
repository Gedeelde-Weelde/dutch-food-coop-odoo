import base64
import io
from unittest.mock import Mock, patch

from PIL import Image

from odoo.addons.product_digi_sync.models.digi_client import DigiClient
from odoo.addons.queue_job.models.base import Base as QueueJobBase

from .digi_sync_base_test_case import DigiSyncBaseTestCase


class ProductTemplateTestCase(DigiSyncBaseTestCase):
    def setUp(self):
        super().setUp()

        def mock_with_delay(with_delay_self):
            return with_delay_self

        self.patcher = patch.object(QueueJobBase, "with_delay", mock_with_delay)
        self.patcher.start()

    def tearDown(self):
        super().tearDown()
        self.patcher.stop()

    @patch("logging.Logger.warning")
    def test_it_logs_an_error_when_plu_code_is_set_but_no_digi_client_is_provided(
        self, mock_logger
    ):
        patched_get_param = self._patch_ir_config_parameter_for_get_param("-1")
        patched_get_param.start()

        product = self.env["product.template"].create(
            {"name": "Test Product Template", "plu_code": 405}
        )
        product.write(
            {
                "name": "Test Product Template",
            }
        )

        mock_logger.assert_called_with(
            "Digi client requested, but no client was configured."
        )
        patched_get_param.stop()

    def test_it_sends_the_product_to_digi_when_plu_code_is_set(self):
        product1 = self.env["product.template"].create(
            {"name": "Test Product Template", "plu_code": 405}
        )
        product2 = self.env["product.template"].create(
            {"name": "Test Product without ply"}
        )

        products = self.env["product.template"].browse([product1.id, product2.id])

        digi_client = self._create_digi_client()

        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            digi_client.id
        )
        patched_get_param.start()
        mock_send_product_to_digi = Mock()
        patch.object(
            DigiClient, "send_product_to_digi", mock_send_product_to_digi
        ).start()
        patch.object(DigiClient, "send_product_image_to_digi", Mock()).start()

        products.write(
            {
                "name": "Test Product Template",
            }
        )

        self.assertEqual(mock_send_product_to_digi.call_args[0][0], product1)
        patched_get_param.stop()

    def _create_digi_client(self):
        digi_client = self.env["product_digi_sync.digi_client"].create(
            {
                "name": "Test Digi Client",
                "username": "user",
                "password": "<PASSWORD>",
            }
        )
        return digi_client

    def test_it_sends_the_product_image_to_digi_when_the_image_is_set(self):
        digi_client = self._create_digi_client()

        client_id = digi_client.id
        patched_get_param = self._patch_ir_config_parameter_for_get_param(client_id)
        patched_get_param.start()
        mock_send_product_image_to_digi = Mock()
        patch.object(
            DigiClient, "send_product_image_to_digi", mock_send_product_image_to_digi
        ).start()
        patch.object(DigiClient, "send_product_to_digi", Mock()).start()

        product = self._create_product_with_image("Test Product Template", 400)

        self.assertEqual(mock_send_product_image_to_digi.call_args[0][0], product)
        patched_get_param.stop()

    def _create_product_with_image(self, name, plu_code):
        product_with_image = self.env["product.template"].create(
            {
                "name": name,
                "plu_code": plu_code,
                "list_price": 1.0,
            }
        )
        # Create a 1x1 pixel image
        image = Image.new("RGB", (1, 1))
        output = io.BytesIO()
        image.save(output, format="PNG")
        # Get the binary data of the image
        image_data = base64.b64encode(output.getvalue())
        output.close()
        product_with_image.image_1920 = image_data
        return product_with_image
