from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestPosConfig(TransactionCase):
    def setUp(self):
        super().setUp()
        self.pos_config = self.env["pos.config"].create({"name": "Test Config"})
        self.coin_product = self.env["product.product"].create(
            {"name": "Connection Coin", "is_connection_coin": True}
        )
        self.regular_product = self.env["product.product"].create(
            {"name": "Regular Product"}
        )

    def test_member_connection_coin_product_accepts_flagged_product(self):
        self.pos_config.member_connection_coin_product_id = self.coin_product
        self.assertEqual(
            self.pos_config.member_connection_coin_product_id, self.coin_product
        )

    def test_non_member_connection_coin_product_accepts_flagged_product(self):
        self.pos_config.non_member_connection_coin_product_id = self.coin_product
        self.assertEqual(
            self.pos_config.non_member_connection_coin_product_id, self.coin_product
        )

    def test_member_connection_coin_product_rejects_unflagged_product(self):
        with self.assertRaises(ValidationError):
            self.pos_config.member_connection_coin_product_id = self.regular_product

    def test_non_member_connection_coin_product_rejects_unflagged_product(self):
        with self.assertRaises(ValidationError):
            self.pos_config.non_member_connection_coin_product_id = self.regular_product
