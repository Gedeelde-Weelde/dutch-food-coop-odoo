import datetime
import logging
import os

from odoo.tests.common import TransactionCase

from odoo.addons.product_import_cwa.models.cwa_product import IncompleteValidationError


class TestProductImportCwa(TransactionCase):
    def setUp(self):
        super().setUp()
        # Set the logging level to WARNING during deletions
        old_logLevel = logging.getLogger("odoo").level
        logging.getLogger("odoo").setLevel(logging.WARNING)
        self.env["cwa.import.product.change"].search([]).unlink()
        self.env["cwa.product"].search([]).unlink()
        self.env["product.supplierinfo"].search([]).unlink()
        self.env["product_food_fields.product_origin"].search([]).unlink()
        logging.getLogger("odoo").setLevel(old_logLevel)

    def reset_translations(self):
        self.env["product.brand"].search([]).unlink()
        self.env["cwa.product.brands"].search([]).unlink()
        self.env["cwa.product.uom"].search([]).unlink()
        self.env["cwa.product.cblcode"].search([]).unlink()
        self.env["cwa.vat.tax"].search([]).unlink()

    def add_translations_for_brand_uom_cblcode_and_tax(self, cwa_prod):
        self.translate_brand(cwa_prod)
        self.translate_uom(cwa_prod)
        self.translate_cblcode(cwa_prod)
        self.translate_tax(cwa_prod)

    def create_origin(self, country_code="CN"):
        return self.env["product_food_fields.product_origin"].create(
            {
                "country_code": country_code,
            }
        )

    def translate_brand(self, prod):
        """Add dummy brand translation to product using wizards"""
        wizard_obj = self.env["cwa.product.import.brands"]
        wizard = wizard_obj.with_context(active_ids=prod.ids).create({})
        wizard.action_apply()

    def translate_uom(self, prod):
        """Add dummy UOM translation to product using wizards"""
        wizard_obj = self.env["cwa.product.import.uom"]
        wizard = wizard_obj.with_context(active_ids=prod.ids).create({})
        uom = self.env.ref("uom.product_uom_kgm")
        wizard.uom_ids.write(dict(uom_id=uom.id, uom_po_id=uom.id))
        wizard.action_apply()

    def translate_cblcode(self, prod):
        """Add dummy CBL code translation to product using wizards"""
        wizard_obj = self.env["cwa.product.import.cblcode"]
        wizard = wizard_obj.with_context(active_ids=prod.ids).create({})
        pos_categ = self.env["pos.category"].create({"name": "Beverage"})
        categ = self.env["product.category"].create({"name": "Beverage"})
        wizard.cblcode_ids.write(
            dict(pos_category=pos_categ.id, internal_category=categ.id)
        )
        wizard.action_apply()

    def translate_cblcode_incomplete(self, prod):
        """Add dummy CBL code translation to product using wizards"""
        wizard_obj = self.env["cwa.product.import.cblcode"]
        wizard = wizard_obj.with_context(active_ids=prod.ids).create({})
        pos_categ = self.env["pos.category"].create({"name": "Beverage"})
        wizard.cblcode_ids.write(
            dict(
                pos_category=pos_categ.id,
            )
        )
        wizard.action_apply()

    def translate_tax(self, prod):
        """Add dummy tax translation to product using wizards"""
        wizard_obj = self.env["cwa.vat.tax.wizard"]
        wizard = wizard_obj.with_context(active_ids=prod.ids).create({})
        account_tax = self.env["account.tax"].create(
            {
                "name": "6 percent",
                "amount": 0.06,
                "amount_type": "percent",
            }
        )
        wizard.tax_ids.write(
            {
                "sale_tax_ids": (6, False, account_tax.ids),
                "purchase_tax_ids": (6, False, account_tax.ids),
            }
        )
        wizard.action_apply()

    def import_first_file(self, cwa_product_obj):
        path = os.path.dirname(os.path.realpath(__file__))
        file1 = os.path.join(path, "data/products_test.xml")
        cwa_product_obj.with_context(new_cursor=False).import_xml_products(file1)

    def import_second_file(self, cwa_product_obj):
        path = os.path.dirname(os.path.realpath(__file__))
        file2 = os.path.join(path, "data/products_test_modified.xml")
        count = cwa_product_obj.with_context(new_cursor=False).import_xml_products(
            file2
        )
        return count

    def import_third_file(self, cwa_product_obj):
        path = os.path.dirname(os.path.realpath(__file__))
        file2 = os.path.join(path, "data/products_test_modified_again.xml")
        count = cwa_product_obj.with_context(new_cursor=False).import_xml_products(
            file2
        )
        return count

    def import_subset_file(self, cwa_product_obj):
        path = os.path.dirname(os.path.realpath(__file__))
        file2 = os.path.join(path, "data/products_test_subset.xml")
        count = cwa_product_obj.with_context(new_cursor=False).import_xml_products(
            file2
        )
        return count

    def test_product_import_cwa_imports_all_records(self):
        cwa_product_obj = self.env["cwa.product"]

        # load first batch of cwa.product records
        path = os.path.dirname(os.path.realpath(__file__))
        file1 = os.path.join(path, "data/products_test.xml")
        count = cwa_product_obj.with_context(new_cursor=False).import_xml_products(
            file1
        )
        self.assertEqual(count, 65)

    def test_product_import_cwa_imports_is_correctly_loaded(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod1 = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.assertEqual(len(cwa_prod1), 1)

    def test_product_import_cwa_load_modified_file(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        count = self.import_second_file(cwa_product_obj)
        self.assertEqual(count, 2)
        cwa_prod2 = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.assertTrue("EEKHOORNS" in cwa_prod2.ingredienten)

    def test_product_import_cwa_translations(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod2 = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.reset_translations()
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod2)
        self.create_origin()
        self.assertEqual(self.env["cwa.product.brands"].search_count([]), 1)
        self.assertEqual(self.env["cwa.product.uom"].search_count([]), 1)
        self.assertEqual(self.env["cwa.product.cblcode"].search_count([]), 1)
        self.assertEqual(self.env["cwa.vat.tax"].search_count([]), 1)

    def test_product_import_with_incomplete_cbl_translation(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.reset_translations()
        self.translate_brand(cwa_prod)
        self.translate_uom(cwa_prod)
        self.translate_cblcode_incomplete(cwa_prod)
        self.translate_tax(cwa_prod)
        self.create_origin()

        with self.assertRaises(IncompleteValidationError):
            cwa_prod.to_product()

    def test_product_import_cwa_product_to_state_imported(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()
        self.assertEqual(cwa_prod.state, "imported")

    def test_product_import_translates_uom_with_ean_always_to_piece_product(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search(
            [("omschrijving", "=", "PRINSESSEN DROOM")], limit=1
        )
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()
        product_template_object = self.env["product.template"]
        imported_product = product_template_object.search(
            [("name", "=", "PRINSESSEN DROOM")]
        )

        self.assertEqual(imported_product.uom_id.name, "Units")

    def test_product_import_cwa_product_import_into_product_template(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()

        product_template_object = self.env["product.template"]
        imported_product = product_template_object.search([("name", "=", "BOEKWEIT")])

        expected_product = {
            "unique_id": "1007-1001",
            "inhoud": "1",
            "eenheid": "KG",
            "verpakkingce": False,
            "herkomst": "CN",
            "ingredients": "INGREDIENTEN: BOEKWEIT",
            "d204": "0",
            "d209": "0",
            "d210": "0",
            "d212": "0",
            "d213": "0",
            "d214": "0",
            "d234": "0",
            "d215": "0",
            "d239": "0",
            "d216": "0",
            "d217": "0",
            "d217b": "0",
            "d220": "0",
            "d221": "0",
            "d221b": "0",
            "d222": "0",
            "d223": "0",
            "d236": "0",
            "d235": "0",
            "d238": "0",
            "d238b": "0",
            "d225": "0",
            "d226": "0",
            "d228": "0",
            "d230": "0",
            "d232": "0",
            "d237": "0",
            "d240": "0",
            "proefdiervrij": "0",
            "vegetarisch": "0",
            "veganistisch": "0",
            "rauwemelk": "0",
        }

        actual_product = {
            key: getattr(imported_product, key, None) for key in expected_product.keys()
        }
        self.maxDiff = None
        self.assertDictEqual(expected_product, actual_product)

    def test_product_import_cwa_supplier_info(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod2 = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod2)
        self.create_origin()
        cwa_prod2.to_product()
        supplierinfo_obj = self.env["product.supplierinfo"]
        supp_info1 = supplierinfo_obj.search([("product_name", "=", "BOEKWEIT")])
        self.assertEqual(len(supp_info1), 1)
        self.assertFalse(supp_info1.eancode)
        self.assertEqual(supp_info1.unique_id, "1007-1001")
        _date = datetime.date(2016, 2, 11)
        self.assertEqual(supp_info1.ingangsdatum, _date)
        self.assertEqual(supp_info1.date_start, _date)
        self.assertEqual(supp_info1.eenheid, "KG")
        self.assertEqual(supp_info1.herkomst, "CN")

    def test_product_import_cwa_handle_multiple_suppliers(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_dup1 = cwa_product_obj.search([("eancode", "=", "8711812421205")])
        self.assertNotEqual(
            cwa_dup1[0].leveranciernummer, cwa_dup1[1].leveranciernummer
        )
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_dup1)
        self.create_origin("NL")
        for rec in cwa_dup1:
            rec.to_product()
        prod1 = self.env["product.template"].search([("eancode", "=", "8711812421205")])
        self.assertEqual(len(prod1), 1)
        self.assertEqual(len(prod1.seller_ids), 2)

    def test_product_import_cwa_supplier_not_deleted(self):
        supplierinfo_obj = self.env["product.supplierinfo"]
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        suppliers_before_import = supplierinfo_obj.search_count([])

        self.import_second_file(cwa_product_obj)

        count = self.import_second_file(cwa_product_obj)
        self.assertEqual(count, 0)
        suppliers_after_import = supplierinfo_obj.search_count([])
        self.assertEqual(suppliers_before_import, suppliers_after_import)

    def test_product_import_cwa_removal(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        path = os.path.dirname(os.path.realpath(__file__))
        file3 = os.path.join(path, "data/products_test_removed.xml")
        count = cwa_product_obj.with_context(new_cursor=False).import_xml_products(
            file3
        )
        self.assertEqual(count, 1)
        self.assertEqual(cwa_product_obj.search_count([]), 64)

    def test_product_import_cwa_recovers_from_invalid_characters_in_xml(self):
        cwa_product_obj = self.env["cwa.product"]

        # load first batch of cwa.product records
        path = os.path.dirname(os.path.realpath(__file__))
        file1 = os.path.join(path, "data/products_test_data_faulty.xml")
        count = cwa_product_obj.with_context(new_cursor=False).import_xml_products(
            file1
        )
        self.assertEqual(count, 2)

    def test_product_import_cwa_updates_supplier_info_when_data_is_changed(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod2 = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod2)
        self.create_origin()
        cwa_prod2.to_product()

        self.import_second_file(cwa_product_obj)

        supplierinfo_obj = self.env["product.supplierinfo"]
        supp_info1 = supplierinfo_obj.search([("product_name", "=", "BOEKWEIT")])
        self.assertEqual("INGREDIENTENN: BOEKWEIT, EEKHOORNS", supp_info1.ingredients)

    def test_only_one_changed_record_is_created_when_an_imported_product_is_updated(
        self
    ):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()

        imported_product = self.env["product.template"].search(
            [("name", "=", "BOEKWEIT")]
        )

        self.import_second_file(cwa_product_obj)

        import_result = self.env["cwa.import.product.change"].search(
            [("affected_product_id", "=", imported_product.id)]
        )

        self.assertEqual(len(import_result), 1)

    def test_a_changed_record_is_created_when_an_imported_product_is_updated(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()

        imported_product = self.env["product.template"].search(
            [("name", "=", "BOEKWEIT")]
        )

        self.import_second_file(cwa_product_obj)

        import_result = self.env["cwa.import.product.change"].search(
            [("affected_product_id", "=", imported_product.id)]
        )

        expected_result = {
            "state": "new",
            "affected_product_id": imported_product.id,
            "affected_product_id_list_price": 3.7,
            "affected_product_id_cost_price": 2.1,
            "product_supplierinfo_list_price": 3.9,
            "product_supplierinfo_cost_price": 2.3,
        }

        actual_result = {
            key: getattr(import_result, key, None)
            for key in expected_result.keys()
            if key != "affected_product_id"
        }
        actual_result["affected_product_id"] = import_result.affected_product_id.id

        self.assertDictEqual(expected_result, actual_result)

    def test_a_changed_record_is_changed_when_an_imported_product_is_updated_again(
        self
    ):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()

        imported_product = self.env["product.template"].search(
            [("name", "=", "BOEKWEIT")]
        )

        self.import_second_file(cwa_product_obj)
        self.import_third_file(cwa_product_obj)

        import_result = self.env["cwa.import.product.change"].search(
            [("affected_product_id", "=", imported_product.id)]
        )

        expected_result = {
            "state": "new",
            "affected_product_id": imported_product.id,
            "affected_product_id_list_price": 3.7,
            "affected_product_id_cost_price": 2.1,
            "product_supplierinfo_list_price": 4.1,
            "product_supplierinfo_cost_price": 2.3,
        }

        actual_result = {
            key: getattr(import_result, key, None)
            for key in expected_result.keys()
            if key != "affected_product_id"
        }
        actual_result["affected_product_id"] = import_result.affected_product_id.id

        self.assertDictEqual(expected_result, actual_result)

    def test_cwa_product_and_the_product_template_are_written(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()

        imported_product = self.env["product.template"].search(
            [("name", "=", "BOEKWEIT")]
        )

        self.import_second_file(cwa_product_obj)

        expected_result = {
            "affected_product_id": imported_product.id,
            "source_cwa_product_id": cwa_prod.id,
        }

        import_result = self.env["cwa.import.product.change"].search(
            [("affected_product_id", "=", imported_product.id)]
        )

        actual_result = {
            "affected_product_id": import_result.affected_product_id.id,
            "source_cwa_product_id": import_result.source_cwa_product_id.id,
        }

        self.assertDictEqual(expected_result, actual_result)

        self.import_second_file(cwa_product_obj)

    def test_boolean_fields_are_imported_correctly_at_first_import(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()

        imported_supplierinfo = self.env["product.supplierinfo"].search(
            [("omschrijving", "=", "BOEKWEIT")]
        )

        self.assertFalse(imported_supplierinfo.weegschaalartikel)
        self.assertFalse(imported_supplierinfo.pluartikel)
        self.assertTrue(imported_supplierinfo.wichtartikel)

    def test_boolean_fields_are_imported_correctly_at_second_import(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()
        self.import_second_file(cwa_product_obj)

        imported_supplierinfo = self.env["product.supplierinfo"].search(
            [("omschrijving", "=", "BOEKWEIT")]
        )

        self.assertFalse(imported_supplierinfo.weegschaalartikel)
        self.assertFalse(imported_supplierinfo.pluartikel)
        self.assertTrue(imported_supplierinfo.wichtartikel)

    def test_a_changed_record_has_a_json_field_for_changes(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()

        imported_product = self.env["product.template"].search(
            [("name", "=", "BOEKWEIT")]
        )

        self.import_second_file(cwa_product_obj)

        import_result = self.env["cwa.import.product.change"].search(
            [("affected_product_id", "=", imported_product.id)]
        )

        changes = {
            "consumentenprijs": {"new": 3.9, "old": 3.7},
            "ingangsdatum": {
                "new": "2017-02-11",
                "old": "2016-02-11",
            },
            "ingredients": {
                "new": "INGREDIENTENN: BOEKWEIT, EEKHOORNS",
                "old": "INGREDIENTEN: BOEKWEIT",
            },
            "inkoopprijs": {"new": 2.3, "old": 2.1},
        }
        result = import_result.value_changes
        self.assertDictEqual(changes, result)

    def test_a_changed_record_has_a_computed_field_for_changed_fields(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()
        cwa_prod.to_product()

        imported_product = self.env["product.template"].search(
            [("name", "=", "BOEKWEIT")]
        )

        self.import_second_file(cwa_product_obj)

        import_result = self.env["cwa.import.product.change"].search(
            [("affected_product_id", "=", imported_product.id)]
        )

        changed_fields = "inkoopprijs, consumentenprijs, ingangsdatum, ingredients"

        self.assertEqual(changed_fields, import_result.changed_fields)

    def test_the_origin_is_imported_in_the_origin_field(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)

        origin = self.create_origin()

        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        cwa_prod.to_product()

        imported_product = self.env["product.template"].search(
            [("name", "=", "BOEKWEIT")]
        )

        self.assertEqual(imported_product.product_origin_id.id, origin.id)

    def test_the_default_product_quality_is_provided_using_data(self):
        imported_quality = self.env["product_food_fields.product_quality"].search(
            [("code", "=", "BIOLOGISCH")]
        )
        self.assertEqual(len(imported_quality), 1)

    def test_the_product_quality_is_imported_in_the_product_quality_field(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)

        expected_quality = self.env["product_food_fields.product_quality"].search(
            [("code", "=", "BIOLOGISCH")]
        )
        self.create_origin()
        cwa_prod.to_product()

        imported_product = self.env["product.template"].search(
            [("name", "=", "BOEKWEIT")]
        )

        self.assertEqual(imported_product.product_quality_id.id, expected_quality.id)

    def test_all_cwa_products_are_returned_to_new_when_product_is_deleted(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_subset_file(cwa_product_obj)

        cwa_prod1 = cwa_product_obj.search([("unique_id", "=", "1001-1263")])
        cwa_prod2 = cwa_product_obj.search([("unique_id", "=", "1039-1263")])

        self.create_origin("NL")
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod1)
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod2)

        cwa_prod1.to_product()
        cwa_prod2.to_product()

        imported_product = self.env["product.template"].search(
            [("eancode", "=", "8714811142843")]
        )

        imported_product.unlink()

        cwa_prod1_changed = cwa_product_obj.search([("unique_id", "=", "1001-1263")])
        cwa_prod2_changed = cwa_product_obj.search([("unique_id", "=", "1039-1263")])

        self.assertEqual(cwa_prod1_changed.state, "new")
        self.assertEqual(cwa_prod2_changed.state, "new")

    def test_when_a_cwa_product_is_imported_twice_it_an_message_is_created(self):
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search([("omschrijving", "=", "BOEKWEIT")])
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin()

        cwa_prod.to_product()
        cwa_prod.to_product()

        self.import_second_file(cwa_product_obj)
        message = self.env["mail.message"].search(
            [("subject", "=", "Duplicate supplier info for product: BOEKWEIT")]
        )

        self.assertEqual(len(message), 1)

    # ruff: noqa: E501
    def test_first_imported_supplier_stays_preferred_supplier_when_a_new_one_is_imported(
        self
    ):
        # ruff: enable
        cwa_product_obj = self.env["cwa.product"]
        self.import_first_file(cwa_product_obj)
        cwa_prod = cwa_product_obj.search(
            [
                ("omschrijving", "=", "SPROOKJES ROOD"),
                ("leveranciernummer", "=", "1001"),
            ]
        )
        self.add_translations_for_brand_uom_cblcode_and_tax(cwa_prod)
        self.create_origin(country_code="NL")
        cwa_prod.to_product()

        other_cwa_prod = cwa_product_obj.search(
            [
                ("omschrijving", "=", "SPROOKJES ROOD"),
                ("leveranciernummer", "=", "1002"),
            ]
        )
        other_cwa_prod.to_product()
        reloaded_product = self.env["product.template"].search(
            [("name", "=", "SPROOKJES ROOD")]
        )

        self.import_second_file(cwa_product_obj)

        self.assertEqual(
            reloaded_product.preferred_supplier_id.leveranciernummer, "1001"
        )
