import base64
import io
from unittest.mock import Mock, patch

from PIL import Image

from odoo.exceptions import ValidationError

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
    def test_it_logs_an_error_when_product_can_bes_send_but_no_digi_client_is_provided(
        self, mock_logger
    ):
        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "digi_client_id", "-1"
        )
        patched_get_param.start()

        product = self.env["product.template"].create(
            {
                "name": "Test Product Template",
                "shop_plucode": 405,
                "send_to_scale": True,
            }
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

    def test_it_sends_the_product_to_digi_when_send_to_scale_is_true(self):
        digi_client = self._create_digi_client()

        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "digi_client_id", digi_client.id
        )
        patched_get_param.start()
        mock_send_product_to_digi = Mock()
        patch.object(
            DigiClient, "send_product_to_digi", mock_send_product_to_digi
        ).start()
        patch.object(DigiClient, "send_product_image_to_digi", Mock()).start()

        product1 = self.env["product.template"].create(
            {
                "name": "Test Product Template",
                "shop_plucode": 405,
                "send_to_scale": True,
            }
        )
        product2 = self.env["product.template"].create(
            {"name": "Test Product without ply"}
        )

        products = self.env["product.template"].browse([product1.id, product2.id])

        products.write(
            {
                "name": "Test Product Template",
            }
        )

        self.assertEqual(mock_send_product_to_digi.call_args[0][0], product1)
        patched_get_param.stop()

    def test_it_does_not_send_the_product_to_digi_when_send_to_scale_is_false(self):
        digi_client = self._create_digi_client()

        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "digi_client_id", digi_client.id
        )
        patched_get_param.start()
        mock_send_product_to_digi = Mock()
        patch.object(
            DigiClient, "send_product_to_digi", mock_send_product_to_digi
        ).start()
        patch.object(DigiClient, "send_product_image_to_digi", Mock()).start()

        product1 = self.env["product.template"].create(
            {
                "name": "Test Product Template",
                "shop_plucode": 405,
                "send_to_scale": False,
            }
        )

        products = self.env["product.template"].browse([product1.id])

        products.write(
            {
                "name": "Test Product Template",
            }
        )

        self.assertEqual(mock_send_product_to_digi.called, False)
        patched_get_param.stop()

    def test_it_sends_the_product_image_to_digi_when_the_image_is_set(self):
        digi_client = self._create_digi_client()

        client_id = digi_client.id
        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "digi_client_id", client_id
        )
        patched_get_param.start()
        mock_send_product_image_to_digi = Mock()
        patch.object(
            DigiClient, "send_product_image_to_digi", mock_send_product_image_to_digi
        ).start()
        patch.object(DigiClient, "send_product_to_digi", Mock()).start()

        product = self._create_product_with_image("Test Product Template", 400)

        self.assertEqual(mock_send_product_image_to_digi.call_args[0][0], product)
        patched_get_param.stop()

    def test_it_sends_the_product_image_to_digi_only_when_new_image_is_written(self):
        digi_client = self._create_digi_client()

        client_id = digi_client.id
        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "digi_client_id", client_id
        )
        patched_get_param.start()
        mock_send_product_image_to_digi = Mock()
        patch.object(
            DigiClient, "send_product_image_to_digi", mock_send_product_image_to_digi
        ).start()
        patch.object(DigiClient, "send_product_to_digi", Mock()).start()

        product = self._create_product_with_image("Test Product Template", 400)
        product.write({"name": "Test changed without image change"})

        self.assertEqual(mock_send_product_image_to_digi.call_count, 1)
        patched_get_param.stop()

    def test_it_sends_the_product_quality_image_to_digi_when_the_quality_is_set(self):
        digi_client = self._create_digi_client()

        client_id = digi_client.id
        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "digi_client_id", client_id
        )
        patched_get_param.start()
        mock_send_product_image_to_digi = Mock()
        patch.object(
            DigiClient,
            "send_product_quality_image_to_digi",
            mock_send_product_image_to_digi,
        ).start()
        patch.object(DigiClient, "send_product_to_digi", Mock()).start()
        patch.object(DigiClient, "send_product_image_to_digi", Mock()).start()

        product = self.env["product.template"].create(
            {
                "name": "test quality",
                "shop_plucode": 42,
                "send_to_scale": True,
                "list_price": 1.0,
            }
        )
        product_quality = self._create_product_quality_with_image()
        product.write(
            {
                "product_quality_id": product_quality.id,
            }
        )

        self.assertEqual(mock_send_product_image_to_digi.call_args[0][0], product)
        patched_get_param.stop()

    def test_it_sends_the_product_quality_image_to_digi_only_when_quality_is_changed(
        self
    ):
        digi_client = self._create_digi_client()

        client_id = digi_client.id
        patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "digi_client_id", client_id
        )
        patched_get_param.start()
        mock_send_product_image_to_digi = Mock()
        patch.object(
            DigiClient,
            "send_product_quality_image_to_digi",
            mock_send_product_image_to_digi,
        ).start()
        patch.object(DigiClient, "send_product_to_digi", Mock()).start()
        patch.object(DigiClient, "send_product_image_to_digi", Mock()).start()

        product = self.env["product.template"].create(
            {
                "name": "test quality",
                "shop_plucode": 42,
                "send_to_scale": True,
                "list_price": 1.0,
            }
        )
        product_quality = self._create_product_quality_with_image()
        product.write(
            {
                "product_quality_id": product_quality.id,
            }
        )
        product.write(
            {
                "name": "test quality not changed so quality has no new image",
            }
        )

        self.assertEqual(mock_send_product_image_to_digi.call_count, 1)
        patched_get_param.stop()

    def test_that_a_plucode_can_always_be_zero(self):
        product1 = self.env["product.template"].create(
            {"name": "Test Product 1", "shop_plucode": 0}
        )
        product2 = self.env["product.template"].create(
            {"name": "Test Product 2", "shop_plucode": 0}
        )
        self.assertEqual(product1.shop_plucode, 0)
        self.assertEqual(product2.shop_plucode, 0)

    def test_that_a_plucode_cannot_have_the_same_value_when_unequal_to_zero(self):
        with self.assertRaises(ValidationError):
            self.env["product.template"].create(
                {"name": "Test Product 1", "shop_plucode": 42}
            )
            self.env["product.template"].create(
                {"name": "Test Product 2", "shop_plucode": 42}
            )

    def _create_product_with_image(self, name, shop_plucode):
        product_with_image = self.env["product.template"].create(
            {
                "name": name,
                "shop_plucode": shop_plucode,
                "send_to_scale": True,
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

    def _create_product_quality_with_image(self):
        return self.env["product_food_fields.product_quality"].create(
            {
                "code": "BD",
                "name": "Biologisch dynamisch",
                "image": self._create_dummy_image("png"),
                "digi_image_id": 42,
            }
        )
