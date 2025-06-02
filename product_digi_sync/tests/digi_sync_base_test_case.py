import base64
import io
from unittest.mock import patch

from PIL import Image

from odoo.tests import TransactionCase

from odoo.addons.base.models.ir_config_parameter import IrConfigParameter


class DigiSyncBaseTestCase(TransactionCase):
    def _patch_ir_config_parameter_for_get_param(self, key_to_patch, value):
        original_get_param = IrConfigParameter.get_param

        def patched_get_param(self, key, default=False):
            if key == key_to_patch:
                return value  # return a specific value for a particular key
            else:
                return original_get_param(self, key, default)

        return patch.object(IrConfigParameter, "get_param", patched_get_param)

    def _patch_ir_config_parameter_for_get_param_with_dict(self, key_values: dict):
        original_get_param = IrConfigParameter.get_param

        def patched_get_param(self, key, default=False):
            if key in key_values.keys():
                return key_values[key]  # return a specific value for a particular key
            else:
                return original_get_param(self, key, default)

        return patch.object(IrConfigParameter, "get_param", patched_get_param)

    def _create_digi_client(self):
        digi_client = self.env["product_digi_sync.digi_client"].create(
            {
                "name": "Test Digi Client",
                "username": "user",
                "password": "<PASSWORD>",
            }
        )
        return digi_client

    @staticmethod
    def _create_dummy_image(target_format):
        image = Image.new("RGB", (1, 1))
        output = io.BytesIO()
        image.save(output, format=target_format)
        # Get the binary data of the image
        image_data = base64.b64encode(output.getvalue())
        output.close()
        return image_data
