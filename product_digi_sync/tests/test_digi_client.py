import base64
import contextlib
import io
import json
from json import JSONDecodeError
from unittest.mock import patch

import requests
from PIL import Image

from odoo.tests import tagged

from odoo.addons.product_digi_sync.models.digi_client import DigiApiException

from .digi_sync_base_test_case import DigiSyncBaseTestCase


class DigiClientTestCase(DigiSyncBaseTestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.digi_client = self.env["product_digi_sync.digi_client"].create(
            {"username": "test_username", "password": "123", "name": "Default"}
        )
        self.patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "weighted_barcode_rule_id", None
        )

    def tearDown(self):
        super().tearDown()
        self.patched_get_param.stop()
        self.patched_get_param = None

    @tagged("post_install", "-at_install")
    def test_it_can_be_instantiated_with_username_and_password(self):
        self.assertEqual(self.digi_client.password, "123")
        self.assertEqual(self.digi_client.username, "test_username")

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_using_the_right_headers_and_url(self):
        product = self.env["product.product"].create({"name": "Test Product"})

        with self.patch_request_post() as post_spy:
            expected_url = "https://fresh.digi.eu:8010/API/V1/ARTICLE.SVC/POST"
            expected_headers = {
                "ApplicationLogIn": json.dumps(
                    {"User": "test_username", "Password": "123"}
                ),
                "Content-Type": "application/json",
            }

            self.digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["url"], expected_url)
            self.assertEqual(post_spy.call_args.kwargs["headers"], expected_headers)

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_with_the_right_payload(self):
        name = "Test product"
        ingredients = "Noten en zo"
        shop_plucode = 200
        expected_unit_price = 250
        expected_cost_price = 150
        expected_storage_temp = 6
        self.patched_get_param.start()

        test_category = self.env["pos.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 42,
            }
        )

        expected_payload = self._create_expected_product_payload(
            cost_price=expected_cost_price,
            unit_price=expected_unit_price,
            ingredients=ingredients,
            name=name,
            shop_plucode=shop_plucode,
            category_id=test_category.external_digi_id,
            show_packed_date_on_label=True,
            storage_temp=expected_storage_temp,
        )

        product = self.env["product.product"].create(
            {
                "name": "Test product",
                "ingredients": ingredients,
                "shop_plucode": shop_plucode,
                "pos_categ_id": test_category.id,
                "list_price": 2.5,
                "standard_price": 1.5,
                "show_packed_date_on_label": True,
                "storage_temperature": expected_storage_temp,
            }
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_with_the_right_payload_when_usage_tips_present(
        self
    ):
        name = "Test product"
        ingredients = "Noten en zo"
        expected_usage_tips = "Gebruikstips"
        shop_plucode = 200
        expected_unit_price = 250
        expected_cost_price = 150
        self.patched_get_param.start()

        test_category = self.env["pos.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 42,
            }
        )

        expected_payload = self._create_expected_product_payload(
            cost_price=expected_cost_price,
            unit_price=expected_unit_price,
            ingredients=ingredients,
            name=name,
            shop_plucode=shop_plucode,
            category_id=test_category.external_digi_id,
            show_packed_date_on_label=True,
            usage_tips=expected_usage_tips,
        )

        product = self.env["product.product"].create(
            {
                "name": "Test product",
                "ingredients": ingredients,
                "shop_plucode": shop_plucode,
                "pos_categ_id": test_category.id,
                "list_price": 2.5,
                "standard_price": 1.5,
                "show_packed_date_on_label": True,
                "usage_tips": expected_usage_tips,
            }
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_with_the_right_payload_with_expiration_dates(
        self
    ):
        name = "Test product"
        ingredients = "Noten en zo"
        shop_plucode = 200
        expected_unit_price = 250
        expected_cost_price = 150
        expected_storage_temp = 6
        self.patched_get_param.start()

        test_category = self.env["pos.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 42,
            }
        )

        expected_use_by_days = 15
        expected_best_before_days = 7

        expected_payload = self._create_expected_product_payload(
            cost_price=expected_cost_price,
            unit_price=expected_unit_price,
            ingredients=ingredients,
            name=name,
            shop_plucode=shop_plucode,
            category_id=test_category.external_digi_id,
            show_packed_date_on_label=True,
            storage_temp=expected_storage_temp,
            use_by_days=expected_use_by_days,
            best_before_days=expected_best_before_days,
        )

        product = self.env["product.product"].create(
            {
                "name": "Test product",
                "ingredients": ingredients,
                "shop_plucode": shop_plucode,
                "pos_categ_id": test_category.id,
                "list_price": 2.5,
                "standard_price": 1.5,
                "show_packed_date_on_label": True,
                "storage_temperature": expected_storage_temp,
                "use_by_days": expected_use_by_days,
                "best_before_days": expected_best_before_days,
            }
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_does_not_send_empty_fields(self):
        name = "Test product"
        ingredients = "Noten en zo"
        shop_plucode = 200
        self.patched_get_param.start()

        test_category = self.env["pos.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 120,
            }
        )

        product_without_standard_price = self.env["product.product"].create(
            {
                "name": "Test product",
                "ingredients": ingredients,
                "shop_plucode": shop_plucode,
                "list_price": 1.0,
                "pos_categ_id": test_category.id,
            }
        )

        expected_payload = self._create_expected_product_payload(
            shop_plucode=shop_plucode,
            name=name,
            ingredients=ingredients,
            unit_price=int(product_without_standard_price.list_price * 100),
            category_id=test_category.external_digi_id,
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product_without_standard_price)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_does_not_send_empty_ingredients(self):
        name = "Test product"
        shop_plucode = 200
        self.patched_get_param.start()

        test_category = self.env["pos.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 120,
            }
        )

        product_without_standard_price = self.env["product.product"].create(
            {
                "name": "Test product",
                "shop_plucode": shop_plucode,
                "list_price": 1.0,
                "pos_categ_id": test_category.id,
            }
        )

        expected_payload = self._create_expected_product_payload(
            shop_plucode=shop_plucode,
            name=name,
            unit_price=int(product_without_standard_price.list_price * 100),
            category_id=test_category.external_digi_id,
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product_without_standard_price)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_sends_status_pieces_article_true_when_article_is_not_weighted_article(
        self
    ):
        name = "Test product"
        shop_plucode = 200
        self.patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "piece_barcode_rule_id", None
        )
        self.patched_get_param.start()

        test_category = self.env["pos.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 120,
            }
        )

        product_without_standard_price = self.env["product.product"].create(
            {
                "name": "Test product",
                "shop_plucode": shop_plucode,
                "list_price": 1.0,
                "pos_categ_id": test_category.id,
                "send_to_scale": True,
                "is_weighted_article": False,
            }
        )

        expected_payload = self._create_expected_product_payload(
            shop_plucode=shop_plucode,
            name=name,
            unit_price=int(product_without_standard_price.list_price * 100),
            category_id=test_category.external_digi_id,
            is_weighted_article=False,
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product_without_standard_price)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_sends_no_barcode_to_digi_id_if_wrong_format(self):
        barcode_rule = self.env["barcode.rule"].create(
            {
                "name": "Test barcode",
                "encoding": "ean13",
                "type": "price",
                "pattern": ".*",
                "digi_barcode_type_id": 42,
            }
        )

        self.patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "weighted_barcode_rule_id", barcode_rule.id
        )
        self.patched_get_param.start()

        product = self.env["product.product"].create(
            {
                "name": "Test product",
            }
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            sended_json = post_spy.call_args.kwargs["data"]
            sended_data = json.loads(sended_json)
            self.assertFalse("NormalBarcode1" in sended_data)

    @tagged("post_install", "-at_install")
    def test_it_sends_the_barcode_digi_id_if_present(self):
        barcode_rule = self.env["barcode.rule"].create(
            {
                "name": "Test barcode",
                "encoding": "ean13",
                "type": "price",
                "pattern": "27.*",
                "digi_barcode_type_id": 42,
            }
        )

        self.patched_get_param = self._patch_ir_config_parameter_for_get_param(
            "weighted_barcode_rule_id", barcode_rule.id
        )
        self.patched_get_param.start()

        product = self.env["product.product"].create(
            {
                "name": "Test product",
            }
        )

        expected_data = {
            "NormalBarcode1": {
                "BarcodeDataType": {
                    "Id": 1,
                },
                "Code": 0,
                "DataId": 42,
                "Flag": 27,
                "Type": {
                    "Id": 1,
                },
            }
        }

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            sent_json = post_spy.call_args.kwargs["data"]
            sent_data = json.loads(sent_json)

            compare_data = {key: sent_data[key] for key in expected_data}

            self.assertEqual(expected_data, compare_data)

    @tagged("post_install", "-at_install")
    def test_it_throws_an_exception_when_request_failed(self):
        product = self.env["product.product"].create({"name": "Test product"})
        response_content = """
                    {
          "Result": -99,
          "ResultDescription": "Invalid_UserPassword",
          "DataId": 0,
          "Post": [],
          "Validation": [{"Description": "just invalid"}]
        }
                    """

        with self.patch_request_post(
            status_code=200, response_content=response_content
        ):
            with self.assertRaises(DigiApiException):
                self.digi_client.send_product_to_digi(product)

    @tagged("post_install", "-at_install")
    def test_it_sets_the_result_description_and_code_as_exception_message(self):
        product = self.env["product.product"].create({"name": "Test product"})
        response_content = """
                    {
          "Result": -98,
          "ResultDescription": "Number of filter parameters not correct",
          "DataId": 0,
          "Post": [],
          "Validation": [{"Description": "extra info"}]
        }
                    """

        with self.patch_request_post(
            status_code=200, response_content=response_content
        ):
            with self.assertRaises(DigiApiException) as context:
                self.digi_client.send_product_to_digi(product)
        self.assertIn(
            "Error -98: Number of filter parameters not correct, reason: extra info",
            str(context.exception),
        )

    def test_it_doesnt_catch_other_exceptions(self):
        product = self.env["product.product"].create({"name": "Test product"})

        with self.patch_request_post(response_content="Invalid json {"):
            with self.assertRaises(JSONDecodeError):
                self.digi_client.send_product_to_digi(product)

    def test_it_sends_a_product_image_to_digi_with_the_right_url(self):
        name = "product Name"
        shop_plucode = 200
        with self.patch_request_post() as post_spy:
            product_with_image = self._create_product_with_image(name, shop_plucode)

            expected_url = "https://fresh.digi.eu:8010/API/V1/MultiMedia.SVC/POST"

            self.digi_client.send_product_image_to_digi(product_with_image)

            self.assertEqual(post_spy.call_args.kwargs["url"], expected_url)

    def test_it_sends_a_product_image_to_digi_with_the_right_payload(self):
        name = "product Name"
        shop_plucode = 200

        with self.patch_request_post() as post_spy:
            product_with_image = self._create_product_with_image(name, shop_plucode)

            expected_image_data = product_with_image.image_1920.decode("utf-8")

            payload = {}
            payload["DataId"] = shop_plucode
            Linknumber_preset_image = 95
            payload["Links"] = [
                {
                    "DataId": shop_plucode,
                    "LinkNumber": Linknumber_preset_image,
                    "Type": {
                        "Description": "Article",
                        "Id": 2,
                    },
                }
            ]
            payload["OriginalInput"] = expected_image_data
            payload["Names"] = [
                {
                    "DataId": 1,
                    "Reference": "Nederlands",
                    "Name": "product_name",
                }
            ]
            payload["InputFormat"] = "png"

            expected_payload = json.dumps(payload)

            self.digi_client.send_product_image_to_digi(product_with_image)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def test_it_sends_a_product_image_to_digi_with_the_right_payload_for_jpeg(self):
        name = "product Name"
        shop_plucode = 200

        with self.patch_request_post() as post_spy:
            product_with_image = self._create_product_with_image_for_jpeg(
                name, shop_plucode
            )

            expected_image_data = product_with_image.image_1920.decode("utf-8")

            payload = {}
            payload["DataId"] = shop_plucode
            linknumber_preset_image = 95
            payload["Links"] = [
                {
                    "DataId": shop_plucode,
                    "LinkNumber": linknumber_preset_image,
                    "Type": {
                        "Description": "Article",
                        "Id": 2,
                    },
                }
            ]
            payload["OriginalInput"] = expected_image_data
            payload["Names"] = [
                {
                    "DataId": 1,
                    "Reference": "Nederlands",
                    "Name": "product_name",
                }
            ]
            payload["InputFormat"] = "jpg"

            expected_payload = json.dumps(payload)

            self.digi_client.send_product_image_to_digi(product_with_image)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def test_it_sends_a_product_quality_image_to_digi_with_the_right_payload(self):
        with self.patch_request_post() as post_spy:
            image_id = 1000010
            quality = self.env["product_food_fields.product_quality"].create(
                {
                    "code": "BD",
                    "name": "Biologisch dynamisch",
                    "image": self._create_dummy_image("png"),
                    "digi_image_id": image_id,
                }
            )

            shop_plucode = 200
            product = self.env["product.template"].create(
                {
                    "name": "test product",
                    "shop_plucode": shop_plucode,
                    "list_price": 1.0,
                    "product_quality_id": quality.id,
                }
            )

            expected_image_data = quality.image.decode("utf-8")

            payload = {}
            payload["DataId"] = image_id
            payload["OriginalInput"] = expected_image_data
            payload["Names"] = [
                {
                    "DataId": 1,
                    "Reference": "Nederlands",
                    "Name": "biologisch_dynamisch",
                }
            ]
            payload["Links"] = [
                {
                    "DataId": shop_plucode,
                    "LinkNumber": 1,
                    "Type": {
                        "Description": "Article",
                        "Id": 2,
                    },
                }
            ]
            payload["InputFormat"] = "png"

            expected_payload = json.dumps(payload)

            self.digi_client.send_product_quality_image_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def test_it_sends_a_product_category_to_digi_with_the_right_url(self):
        category_name = "Test category"
        digi_id = 2
        category = self.env["pos.category"].create(
            {
                "name": category_name,
                "external_digi_id": digi_id,
            }
        )

        with self.patch_request_post() as post_spy:
            expected_url = "https://fresh.digi.eu:8010/API/V1/MAINGROUP.SVC/POST"

            self.digi_client.send_category_to_digi(category)

            self.assertEqual(post_spy.call_args.kwargs["url"], expected_url)

    def test_it_sends_a_category_digi(self):
        category_name = "Test category"
        digi_id = 2
        category = self.env["pos.category"].create(
            {
                "name": category_name,
                "external_digi_id": digi_id,
            }
        )

        payload = {
            "DataId": digi_id,
            "DepartmentId": 97,
            "Names": [
                {
                    "Reference": "Nederlands",
                    "Name": category_name,
                }
            ],
        }

        expected_payload = json.dumps(payload)

        with self.patch_request_post() as post_spy:
            self.digi_client.send_category_to_digi(category)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def test_it_sends_a_product_origin_to_digi_with_the_right_payload(self):
        origin = self.env["product_food_fields.product_origin"].create(
            {"name": "Spanje"}
        )

        payload = {
            "DataId": origin.external_digi_id,
            "Names": [
                {
                    "Reference": "Nederlands",
                    "DdData": "02000000"
                    "<span style='font-family:\"DejaVu Sans\";font-size:24px;'>"
                    "Herkomst:"
                    "</span><b><span style='font-family:\"DIN\";font-size:36px;'>"
                    "Spanje"
                    "</span></b>",  # noqa: E501, pylint: disable=W1401
                    "Name": "Herkomst Spanje",
                }
            ],
        }

        expected_payload = json.dumps(payload)

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_origin_to_digi(origin)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def test_it_sends_the_product_origin_to_digi_using_labeltext_with_digi_id(self):
        origin = self.env["product_food_fields.product_origin"].create(
            {"name": "Spanje"}
        )
        product = self.env["product.product"].create(
            {"name": "Test Origin", "shop_plucode": 42, "product_origin_id": origin.id}
        )

        expected_labeltext_in_payload = origin.external_digi_id

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            send_data = json.loads(post_spy.call_args.kwargs["data"])
            self.assertEqual(
                send_data["LabelText6DataId"], expected_labeltext_in_payload
            )

    def test_it_sends_the_product_branch_as_extra_info_in_the_commodity_field_to_digi(
        self
    ):
        brand = self.env["product.brand"].create({"name": "ACME"})
        product = self.env["product.product"].create(
            {
                "name": "Test Origin",
                "shop_plucode": 42,
                "product_brand_id": brand.id,
            }
        )
        expected_commodity_payload = (
            "08010000Test Origin~05010000ACME~01000000~01000000"
        )
        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            send_data = json.loads(post_spy.call_args.kwargs["data"])
            self.assertEqual(
                send_data["Names"][0]["DdFormatCommodity"], expected_commodity_payload
            )

    def test_it_sends_active_in_scale_as_true_when_product_is_active(self):
        shop_plucode = 42
        name = "Test Active"
        product = self.env["product.product"].create(
            {
                "name": name,
                "shop_plucode": shop_plucode,
            }
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            send_data = json.loads(post_spy.call_args.kwargs["data"])

            self.assertTrue(send_data["StatusFields"]["ActiveInScale"])

    def test_it_sends_active_in_scale_as_false_when_product_is_inactive(self):
        shop_plucode = 42
        name = "Test Active"
        product = self.env["product.product"].create(
            {
                "name": name,
                "active": False,
                "shop_plucode": shop_plucode,
            }
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            send_data = json.loads(post_spy.call_args.kwargs["data"])

            self.assertFalse(send_data["StatusFields"]["ActiveInScale"])

    @contextlib.contextmanager
    def patch_request_post(self, status_code=200, response_content=None):
        if not response_content:
            response_content = json.dumps(
                {
                    "Result": 1,
                    "ResultDescription": "Ok",
                    "DataId": 0,
                    "Post": [],
                    "Validation": [],
                }
            )
        mock_response = requests.Response()
        mock_response.status_code = status_code
        mock_response._content = response_content.encode("utf-8")
        with patch("requests.post", return_value=mock_response) as post_spy:
            yield post_spy

    def _create_product_with_image(self, name, shop_plucode):
        product_with_image = self.env["product.template"].create(
            {
                "name": name,
                "shop_plucode": shop_plucode,
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

    def _create_product_with_image_for_jpeg(self, name, shop_plucode):
        product_with_image = self.env["product.template"].create(
            {
                "name": name,
                "shop_plucode": shop_plucode,
                "list_price": 1.0,
            }
        )
        # Create a 1x1 pixel image
        image_data = self._create_dummy_image(target_format="jpeg")
        product_with_image.image_1920 = image_data
        return product_with_image

    def _create_expected_product_payload(self, **kwargs):
        data = {}
        data["DataId"] = kwargs.get("shop_plucode")
        data["Names"] = [
            {
                "Reference": "Nederlands",
                "DdFormatCommodity": f"08010000{kwargs.get('name')}~01000000",
            }
        ]
        if kwargs.get("ingredients"):
            data["Names"][0][
                "DdFormatIngredient"
            ] = f"04000000Ingrediënten: {kwargs.get('ingredients')}~01000000~01000000"
        if kwargs.get("usage_tips"):
            data["Names"][0][
                "DdFormatSpecialMessage"
            ] = f"04000000<br>{kwargs.get('usage_tips')}~01000000"
        if kwargs.get("unit_price"):
            data["UnitPrice"] = kwargs.get("unit_price")
        if kwargs.get("cost_price"):
            data["CostPrice"] = kwargs.get("cost_price")
        data["MainGroupDataId"] = kwargs.get("category_id")

        data["StatusFields"] = {
            "ActiveInScale": True,
            "PiecesArticle": not kwargs.get("is_weighted_article", True),
            "PackedDate": kwargs.get("show_packed_date_on_label") or False,
            "ShowMinStorageTemp": True if kwargs.get("storage_temp") else False,
        }
        data["StatusFields"]["SellByDate"] = False
        data["StatusFields"]["TasteDate"] = False
        if kwargs.get("storage_temp"):
            data["MinStorageTemp"] = kwargs.get("storage_temp")
        if kwargs.get("use_by_days"):
            data["StatusFields"]["SellByDate"] = True
            data["SellByDateAmount"] = kwargs.get("use_by_days")
        if kwargs.get("best_before_days"):
            data["StatusFields"]["TasteDate"] = True
            data["TasteDateAmount"] = kwargs.get("best_before_days")
        return json.dumps(data)
