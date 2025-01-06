import logging
import re

from odoo import api, fields, models
from odoo.tools import get_barcode_check_digit

from odoo.addons.queue_job.exception import RetryableJobError

from .digi_sync_base_model import DigiSyncBaseModel

_logger = logging.getLogger(__name__)


class ProductTemplate(DigiSyncBaseModel, models.Model):
    _inherit = "product.template"

    shop_plucode = fields.Integer(string="Shop plucode", required=False, default=None)
    send_to_scale = fields.Boolean(string="Send to scale", required=False)
    is_weighted_article = fields.Boolean(
        string="Weighted article", required=False, default=True
    )
    product_brand_id = fields.Many2one("product.brand", string="Product brand")
    show_packed_date_on_label = fields.Boolean(
        string="Show packed date on label", required=False
    )

    def get_current_barcode_rule(self):
        weighted_barcode_rule = self._get_barcode_rule("weighted_barcode_rule_id")
        piece_barcode_rule = self._get_barcode_rule("piece_barcode_rule_id")

        return weighted_barcode_rule if self.is_weighted_article else piece_barcode_rule

    @api.depends("shop_plucode", "is_weighted_article", "send_to_scale")
    def _compute_barcode(self):
        for record in self:
            if not record.send_to_scale or not record.shop_plucode:
                return super()._compute_barcode()
            current_rule = record.get_current_barcode_rule()
            if current_rule is not None:
                record.set_barcode(current_rule)

    def set_barcode(self, rule):
        pattern = rule.pattern
        is_ean = rule.encoding == "ean13"
        self.barcode = self._prepare_barcode(pattern, self.shop_plucode, is_ean)

    @staticmethod
    def _prepare_barcode(barcode_pattern, shop_plucode, is_ean13):
        # Converting the code to a padded string
        code_str = str(shop_plucode)
        code_length = barcode_pattern.count(".")
        padded_code = code_str.zfill(code_length)

        # Building the dot pattern for regex search
        dot_pattern = r"\.{" + str(code_length) + "}"

        # Replacing the specific number of dots with the padded code
        barcode = re.sub(dot_pattern, padded_code, barcode_pattern, count=1, flags=0)

        # Replacing whatever is inside the {} brackets with zeros
        repl_length = (
            len(re.findall(r"{.*}", barcode_pattern)[0]) - 2
        )  # subtract 2 for the {} brackets
        zeros = "0" * repl_length
        barcode = re.sub(r"{.*}", zeros, barcode, count=0, flags=0)
        if is_ean13:
            barcode_check_digit = get_barcode_check_digit(barcode + "0")
            barcode = f"{barcode}{barcode_check_digit}"

        return barcode

    def _get_barcode_rule(self, rule_id):
        barcode_rule_id = self.env["ir.config_parameter"].get_param(rule_id)
        if barcode_rule_id:
            return self.env["barcode.rule"].browse(int(barcode_rule_id))
        return None

    def write(self, vals):
        result = super().write(vals)
        for product_template in self:
            if product_template.should_send_to_digi():
                product_template.send_to_digi()
                if "image_1920" in vals.keys():
                    product_template.send_image_to_digi()
                if "product_quality_id" in vals.keys():
                    product_template.send_quality_image_to_digi()
        return result

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if record.should_send_to_digi():
            record.send_to_digi()
            record.send_image_to_digi()
            record.send_quality_image_to_digi()

        return record

    def should_send_to_digi(self):
        return self.send_to_scale and self.shop_plucode

    def send_to_digi_directly(self):
        client = self._get_digi_client()
        if client:
            try:
                client.send_product_to_digi(self)
            except Exception as e:
                raise RetryableJobError(str(e), 5) from e

    def send_image_to_digi(self):
        self.ensure_one()
        if not self.image_1920:
            return
        self.with_delay().send_image_to_digi_directly()

    def send_image_to_digi_directly(self):
        client = self._get_digi_client()
        if client:
            try:
                client.send_product_image_to_digi(self)
            except Exception as e:
                raise RetryableJobError(str(e), 5) from e

    def send_quality_image_to_digi(self):
        self.ensure_one()
        if not self.product_quality_id.image:
            return
        self.with_delay().send_quality_image_to_digi_directly()

    def send_quality_image_to_digi_directly(self):
        client = self._get_digi_client()
        if client:
            try:
                client.send_product_quality_image_to_digi(self)
            except Exception as e:
                raise RetryableJobError(str(e), 5) from e
