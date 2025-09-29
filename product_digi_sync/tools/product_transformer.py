import base64
import io
import json
import re

from PIL import Image


class ProductTransformer:
    @classmethod
    def transform_product_to_payload(self, product, language_code):
        data = {}
        data["DataId"] = product.shop_plucode
        commodity = f"08010000{product.name}"
        if product.product_brand_id:
            commodity += (
                f"~05010000" f"{product.product_brand_id.name}" f"~01000000~01000000"
            )
        else:
            commodity += "~01000000"
        data["Names"] = [
            {
                "Reference": language_code,
                "DdFormatCommodity": commodity,
            }
        ]
        if product.ingredients:
            data["Names"][0][
                "DdFormatIngredient"
            ] = f"04000000Ingrediënten: {product.ingredients}~01000000~01000000"
        if product.usage_tips:
            data["Names"][0][
                "DdFormatSpecialMessage"
            ] = f"04000000<br>{product.usage_tips}~01000000"
        if product.list_price:
            data["UnitPrice"] = int(product.list_price * 100)
        if product.standard_price:
            data["CostPrice"] = int(product.standard_price * 100)
        if product.pos_categ_id.id:
            data["MainGroupDataId"] = product.pos_categ_id.external_digi_id
        if product.product_origin_id:
            data["LabelText6DataId"] = product.product_origin_id.external_digi_id
        data["StatusFields"] = {
            "ActiveInScale": product.available_in_pos,
            "Active": product.available_in_pos,
            "PiecesArticle": not product.is_weighted_article,
            "PackedDate": product.show_packed_date_on_label,
            "ShowMinStorageTemp": False,
            "SellByDate": False,
            "TasteDate": False,
        }
        if product.storage_temperature != 0:
            data["StatusFields"]["ShowMinStorageTemp"] = True
            data["MinStorageTemp"] = product.storage_temperature
        if product.use_by_days != 0:
            data["StatusFields"]["SellByDate"] = True
            data["SellByDateAmount"] = product.use_by_days
        if product.best_before_days != 0:
            data["StatusFields"]["TasteDate"] = True
            data["TasteDateAmount"] = product.best_before_days
        if product and product.get_current_barcode_rule() is not None:
            barcode_rule = product.get_current_barcode_rule()
            matches = re.match(r"^(\d{2}).*", barcode_rule.pattern)

            if matches:
                flag = matches.group(1)
                if flag.isnumeric():
                    barcode_id = barcode_rule.digi_barcode_type_id
                    data["NormalBarcode1"] = {
                        "BarcodeDataType": {
                            "Id": 1,
                        },
                        "Code": 0,
                        "DataId": barcode_id,
                        "Flag": int(flag),
                        "Type": {
                            "Id": 1,
                        },
                    }

        return json.dumps(data)

    @classmethod
    def transform_product_to_image_payload(cls, product, language_code):
        image_name = product.name.lower().replace(" ", "_")
        payload = {"DataId": product.shop_plucode}
        image_data = base64.b64decode(product.image_1920)
        image = Image.open(io.BytesIO(image_data))
        image_format = image.format.lower().replace("jpeg", "jpg")
        payload["Links"] = [
            {
                "DataId": product.shop_plucode,
                "LinkNumber": 95,
                "Type": {
                    "Description": "Article",
                    "Id": 2,
                },
            }
        ]
        payload["OriginalInput"] = product.image_1920.decode("utf-8")
        payload["Names"] = [
            {
                "DataId": 1,
                "Reference": language_code,
                "Name": image_name,
            }
        ]
        payload["InputFormat"] = image_format
        return json.dumps(payload)

    @classmethod
    def transform_product_category_to_payload(cls, product_category, language_code):
        payload = {
            "DataId": product_category.external_digi_id,
            "DepartmentId": 97,
            "Names": [
                {
                    "Reference": language_code,
                    "Name": product_category.name,
                }
            ],
        }
        return json.dumps(payload)

    @classmethod
    def transform_product_origin_to_payload(cls, product_origin, language_code):
        payload = {
            "DataId": product_origin.external_digi_id,
            "Names": [
                {
                    "Reference": language_code,
                    "DdData": f"02000000"
                    f"<span style='font-family:\"DejaVu Sans\";font-size:24px;'>"
                    f"Herkomst:"
                    f"</span><b><span style='font-family:\"DIN\";font-size:36px;'>"
                    f"{product_origin.name}"
                    f"</span></b>",
                    "Name": f"Herkomst {product_origin.name}",
                }
            ],
        }

        return json.dumps(payload)

    @classmethod
    def transform_product_quality_to_image_payload(cls, product, language_code):
        product_quality = product.product_quality_id
        image_name = product_quality.name.lower().replace(" ", "_")
        payload = {"DataId": product_quality.digi_image_id}
        image_data = base64.b64decode(product_quality.image)
        image = Image.open(io.BytesIO(image_data))
        image_format = image.format.lower().replace("jpeg", "jpg")
        payload["OriginalInput"] = product_quality.image.decode("utf-8")
        payload["Names"] = [
            {
                "DataId": 1,
                "Reference": language_code,
                "Name": image_name,
            }
        ]
        payload["Links"] = [
            {
                "DataId": product.shop_plucode,
                "LinkNumber": 1,
                "Type": {
                    "Description": "Article",
                    "Id": 2,
                },
            }
        ]
        payload["InputFormat"] = image_format
        return json.dumps(payload)
