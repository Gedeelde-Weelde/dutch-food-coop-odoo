import ftplib
import logging
import os
from datetime import date

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

from .utils import PRESENCE_SELECTION, YESNO_SELECTION, XMLProductLoader, split_data

_logger = logging.getLogger(__name__)

CHUNKSIZE = 50

# Fields to transfer to supplier info
FIELDS_TO_SUPPLIER_INFO = (
    "eancode",
    "omschrijving",
    "weegschaalartikel",
    "wichtartikel",
    "pluartikel",
    "inhoud",
    "eenheid",
    "verpakkingce",
    "merk",
    "kwaliteit",
    "btw",
    "cblcode",
    "bestelnummer",
    "proefdiervrij",
    "vegetarisch",
    "veganistisch",
    "rauwemelk",
    "inkoopprijs",
    "consumentenprijs",
    "ingangsdatum",
    "herkomst",
    "ingredienten",
    "statiegeld",
    "kassaomschrijving",
    "plucode",
    "sve",
    "status",
    "keurmerkbio",
    "keurmerkoverig",
    "herkomstregio",
    "aantaldagenhoudbaar",
    "bewaartemperatuur",
    "gebruikstips",
    "lengte",
    "breedte",
    "hoogte",
    "code",
    "d204",
    "d209",
    "d210",
    "d212",
    "d213",
    "d214",
    "d234",
    "d215",
    "d239",
    "d216",
    "d217",
    "d217b",
    "d220",
    "d221",
    "d221b",
    "d222",
    "d223",
    "d236",
    "d235",
    "d238",
    "d238b",
    "d225",
    "d226",
    "d228",
    "d230",
    "d232",
    "d237",
    "d240",
    "d241",
    "d242",
    "pos_categ_id",
    "leveranciernummer",
)

# Which fields to load from XML
FIELDS_TO_LOAD = FIELDS_TO_SUPPLIER_INFO + (
    (None, "unique_id"),
    (None, "hash"),
)

KEY_MAPPINGS_CWA_TO_PRODUCT = {
    "ingredienten": "ingredients",
    "gebruikstips": "usage_tips",
    "bewaartemperatuur": "storage_temperature",
    "aantaldagenhoudbaar": "use_by_days",
}


class IncompleteValidationError(UserError):
    pass


def map_key(key):
    if key in KEY_MAPPINGS_CWA_TO_PRODUCT:
        return KEY_MAPPINGS_CWA_TO_PRODUCT[key]
    return key


class CwaProduct(models.Model):
    _name = "cwa.product"
    _description = "CWA product"

    state = fields.Selection(
        [
            ("new", "New"),
            ("imported", "Imported"),
        ],
        default="new",
    )
    name = fields.Char("Product name", related="omschrijving")
    vendor_id = fields.Many2one(
        "res.partner",
        "Leverancier",
        compute="_compute_vendor_id",
        search="_search_vendor_id",
        help="Vendor of this product",
    )
    unique_id = fields.Char(index=True)
    eancode = fields.Char(help="EAN code")
    weegschaalartikel = fields.Boolean()
    wichtartikel = fields.Boolean()
    pluartikel = fields.Boolean()
    inhoud = fields.Char(help="Inhoud van de verpakking.")
    eenheid = fields.Char(help="Eenheid van de inhoud.")
    verpakkingce = fields.Char(help="Verpakking van consumenteneenheid.")
    merk = fields.Char(help="merk.")
    kwaliteit = fields.Char(help="Kwaliteitsaanduiding.")
    btw = fields.Char(help="BTW percentage 0, 6 of 21")
    cblcode = fields.Char(help="cblcode")
    leveranciernummer = fields.Char(help="Nummer van de leverancier.")
    bestelnummer = fields.Char(help="Bestelnummer van artikel bij leverancier.")
    proefdiervrij = fields.Selection(YESNO_SELECTION)
    vegetarisch = fields.Selection(YESNO_SELECTION)
    veganistisch = fields.Selection(YESNO_SELECTION)
    rauwemelk = fields.Selection(YESNO_SELECTION)
    inkoopprijs = fields.Float(help="inkoopprijs")
    consumentenprijs = fields.Float("Adviesprijs", help="consumentenprijs")
    ingangsdatum = fields.Date(help="Ingangsdatum van product")
    herkomst = fields.Char(help="Land van herkomst in vorm ISO 3166 code.")
    ingredienten = fields.Text(help="Beschrijving van de ingredienten.")
    statiegeld = fields.Float(help="Statiegeldbedrag.")
    omschrijving = fields.Char(help="Omschrijving van het product")
    kassaomschrijving = fields.Char(
        help="Korte omschrijving van het product tbv de kassa"
    )
    plucode = fields.Char(help="4-cijferige plucode.")
    sve = fields.Char(help="Standaard verpakkingseenheid bij leverancier.")
    status = fields.Char(help="Mogelijke waarden: Actief/Non Actief/Gesaneerd")
    keurmerkbio = fields.Char(help="keurmerkbio")
    keurmerkoverig = fields.Char(help="keurmerkoverig")
    herkomstregio = fields.Char(help="Regio van herkomst")
    aantaldagenhoudbaar = fields.Char(help="Aantal dagen houdbaar")
    bewaartemperatuur = fields.Char(help="bewaartemperatuur")
    gebruikstips = fields.Char(help="gebruikstips")
    lengte = fields.Char(help="lengte")
    breedte = fields.Char(help="breedte")
    hoogte = fields.Char(help="hoogte")
    code = fields.Char(help="code")
    d204 = fields.Selection(PRESENCE_SELECTION, help="Cacao")
    d209 = fields.Selection(PRESENCE_SELECTION, help="Glutamaat")
    d210 = fields.Selection(PRESENCE_SELECTION, help="Gluten")
    d212 = fields.Selection(PRESENCE_SELECTION, help="Ei")
    d213 = fields.Selection(PRESENCE_SELECTION, help="Kip")
    d214 = fields.Selection(PRESENCE_SELECTION, help="Melk")
    d234 = fields.Selection(PRESENCE_SELECTION, help="Koriander")
    d215 = fields.Selection(PRESENCE_SELECTION, help="Lactose")
    d239 = fields.Selection(PRESENCE_SELECTION, help="Lupine")
    d216 = fields.Selection(PRESENCE_SELECTION, help="Mais")
    d217 = fields.Selection(PRESENCE_SELECTION, help="Noten")
    d217b = fields.Selection(PRESENCE_SELECTION, help="Notenolie")
    d220 = fields.Selection(PRESENCE_SELECTION, help="Peulvruchten")
    d221 = fields.Selection(PRESENCE_SELECTION, help="Pinda")
    d221b = fields.Selection(PRESENCE_SELECTION, help="Pindaolie")
    d222 = fields.Selection(PRESENCE_SELECTION, help="Rogge")
    d223 = fields.Selection(PRESENCE_SELECTION, help="Rundvlees")
    d236 = fields.Selection(PRESENCE_SELECTION, help="Schaaldieren")
    d235 = fields.Selection(PRESENCE_SELECTION, help="Selderij")
    d238 = fields.Selection(PRESENCE_SELECTION, help="Sesam")
    d238b = fields.Selection(PRESENCE_SELECTION, help="Sesamolie")
    d225 = fields.Selection(PRESENCE_SELECTION, help="Soja")
    d226 = fields.Selection(PRESENCE_SELECTION, help="Soja-olie")
    d228 = fields.Selection(PRESENCE_SELECTION, help="Sulfiet")
    d230 = fields.Selection(PRESENCE_SELECTION, help="Tarwe")
    d232 = fields.Selection(PRESENCE_SELECTION, help="Varkensvlees")
    d237 = fields.Selection(PRESENCE_SELECTION, help="Vis")
    d240 = fields.Selection(PRESENCE_SELECTION, help="Wortel")
    d241 = fields.Selection(PRESENCE_SELECTION, help="Mosterd")
    d242 = fields.Selection(PRESENCE_SELECTION, help="Weekdieren")
    pos_categ_id = fields.Char(
        "NOT A REFERENCE", help="Not a reference field, just a char field."
    )
    hash = fields.Char(required=True)

    def write(self, vals):
        result = super().write(vals)
        # TODO: This triggers very weird behaviour. Please fix after testing
        # (GED-24)
        for cwa_product in self:
            keys_write_now = set(vals.keys())
            if not keys_write_now.intersection(FIELDS_TO_SUPPLIER_INFO):
                continue

            ## Find if this product has been transferred to a supplier info model
            supplier_info = self.env["product.supplierinfo"].search(
                [("unique_id", "=", cwa_product.unique_id)]
            )
            if len(supplier_info) > 1:
                supplier_info = supplier_info[0]
                self._send_supplierinfo_duplicate_message(supplier_info)

            if supplier_info:
                supplier_info_vals = {
                    map_key(key): getattr(self, key) for key in FIELDS_TO_SUPPLIER_INFO
                }
                self._detect_product_changes(
                    cwa_product, supplier_info, supplier_info_vals
                )
                supplier_info.write(supplier_info_vals)
        return result

    def _send_supplierinfo_duplicate_message(self, supplier_info):
        channel = self._get_or_create_mail_channel()
        body = (
            f"Please check product with name: "
            f"{supplier_info.product_name} and product template id: "
            f"{supplier_info.product_tmpl_id}"
        )
        subject = f"Duplicate supplier info for product: {supplier_info.product_name}"

        _logger.warning(body)

        channel.message_post(
            subject=subject,
            body=body,
        )

    def _get_or_create_mail_channel(self):
        channel = (
            self.env["mail.channel"]
            .sudo()
            .search([("name", "=", "Announcements")], limit=1)
        )
        if not channel:
            channel = (
                self.env["mail.channel"]
                .sudo()
                .create(
                    {
                        "name": "Announcements",
                        "channel_type": "channel",
                    }
                )
            )
        return channel

    @api.model
    def parse_from_xml(self, prod_file):
        cwa_product_model = self.env["cwa.product"]

        loader = XMLProductLoader(cwa_product_model)

        return loader.parse_from_xml(prod_file)

    @api.model
    def update_records(self, records, model):
        count = 0
        for record in records:
            rec = self.env[model].search([("unique_id", "=", record["unique_id"])])
            if rec:
                rec.write(record)
                count += 1
        return count

    def _detect_product_changes(self, cwa_product, supplier_info, supplier_info_vals):
        if cwa_product.eancode:
            product_tmpl = self.env["product.template"].search(
                [("eancode", "=", cwa_product.eancode)]
            )
        else:
            product_tmpl = self.env["product.template"].search(
                [("unique_id", "=", cwa_product.unique_id)]
            )

        if product_tmpl:
            changes = self._get_value_changes(supplier_info_vals, supplier_info)
            cwa_import_product_change_model = self.env["cwa.import.product.change"]
            state = "new"
            if product_tmpl.preferred_supplier_id and (
                supplier_info.id != product_tmpl.preferred_supplier_id.id
            ):
                state = "no-preferred-new"
            new_vals = {
                "state": state,
                "affected_product_id": product_tmpl.id,
                "source_cwa_product_id": cwa_product.id,
                "value_changes": changes,
            }
            # Try to find an existing change model
            existing = cwa_import_product_change_model.search(
                [("source_cwa_product_id", "=", cwa_product.id)]
            )
            if existing:
                existing.write(new_vals)
            else:
                cwa_import_product_change_model.create(new_vals)

    def _get_value_changes(self, new_vals, supplier_info):
        changes = {}
        if supplier_info:
            for field in new_vals:
                old_value = getattr(supplier_info, field, None)
                new_value = new_vals[field]
                if old_value != new_value:
                    changes[field] = {
                        "old": self._check_date_and_fix_if_date(old_value),
                        "new": self._check_date_and_fix_if_date(new_value),
                    }
        return changes

    def _check_date_and_fix_if_date(self, value):
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")  # Convert date to 'YYYY-MM-DD'
        return value

    @api.model
    def load_records(self, keys, data, model):
        data_chunks = split_data(data, split_size=CHUNKSIZE)
        count_successful = 0
        for data_subset in data_chunks:
            for attempt in range(5):
                use_fresh_cursor = self.env.context.get("new_cursor", False)
                if use_fresh_cursor:
                    _logger.info("new cursor created")
                    new_cr = self.pool.cursor()
                    uid, context = self.env.uid, self.env.context
                    env = api.Environment(new_cr, uid, context)
                else:
                    env = self.env

                try:
                    x = env[model].load(keys, data_subset)
                    if len(x["messages"]) > 0:
                        _logger.warning("attempt..%s" % attempt)
                        _logger.error(x)
                        continue
                    else:
                        _logger.warning("success..%s" % attempt)
                        if use_fresh_cursor:
                            env.cr.commit()
                        count_successful += len(x["ids"])
                        break

                finally:
                    if use_fresh_cursor:
                        env.cr.close()

        return count_successful

    @api.model
    def delete_records(self, unique_ids, model):
        for unique_id in unique_ids:
            self.env[model].search([("unique_id", "=", unique_id)]).unlink()
        return len(unique_ids)

    @api.model
    def import_xml_products(self, prod_file):
        if not prod_file:
            prod_file = self._get_prod_file_from_ftp()
        if not prod_file:
            _logger.error("XML file not found!")
            return

        keys, to_load, to_update, to_delete = self.parse_from_xml(prod_file)
        count = 0
        if to_load:
            count += self.load_records(keys, to_load, "cwa.product")
        if to_update:
            count += self.update_records(to_update, "cwa.product")
        if to_delete:
            count += self.delete_records(to_delete, "cwa.product")

        supplierinfo = self.env["product.supplierinfo"].search([], limit=500)
        if supplierinfo:  # Only compare prices if we have records
            supplierinfo.compare_prices()
        return count

    @api.model
    def import_demo_xml_products(self):
        path = os.path.dirname(os.path.realpath(__file__))
        prod_file = os.path.join(path, "../tests/data/products_test.xml")
        self.import_xml_products(prod_file)

    def to_product(self):
        """
        This is the main CWA import function.
        It imports a CWA product to a product.supplierinfo
        record, then couples to a product.template.
        If it cannot decode the CWA product well, it throws
        a ValidationError.
        """
        self.ensure_one()

        try:
            # product.supplierinfo values
            if not self.vendor_id:
                raise ValidationError(
                    _("Uknown vendor for this product. Fill the vendor first")
                )

            supplier_product_info_dict = self._create_supplier_load_dict()

            # extra product.template values
            extra_prod_dict = {}

            self._translate_standard_unit_of_packiging(supplier_product_info_dict)

            try:
                self._translate_brand(extra_prod_dict)
            except ValidationError:
                return {
                    "type": "ir.actions.act_window",
                    "name": "Translate Brand",
                    "res_model": "cwa.brand.translation.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": {"default_brand_name": self.merk},
                }

            try:
                self._translate_uoms(extra_prod_dict)
            except ValidationError:
                return {
                    "type": "ir.actions.act_window",
                    "name": "Translate UOMs",
                    "res_model": "cwa.uom.translation.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": {
                        "default_eenheid": self.eenheid,
                        "default_inhoud": self.inhoud,
                    },
                }

            try:
                self._translate_cbl_codes(extra_prod_dict)
            except ValidationError:
                return {
                    "type": "ir.actions.act_window",
                    "name": "Translate CBL Codes",
                    "res_model": "cwa.cblcode.translation.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": {
                        "default_source_value": self.cblcode,
                    },
                }

            self._translate_quality(extra_prod_dict)

            self._translate_product_quality(extra_prod_dict)

            self._translate_vat(extra_prod_dict)

            try:
                self._translate_product_origin(extra_prod_dict)
            except ValidationError:
                return {
                    "type": "ir.actions.act_window",
                    "name": "Translate Product Origin",
                    "res_model": "cwa.product.origin.translation.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": {
                        "default_country_code": self.herkomst,
                    },
                }

            # Search if a product with this EAN code already exists
            prod_obj = self.env["product.template"]
            products_by_same_unique_code = prod_obj.search(
                [("unique_id", "=", self.unique_id)]
            )
            products_by_same_ean_code = self.eancode and prod_obj.search(
                [("eancode", "=", self.eancode)]
            )
            # Create new product if the eancode is missing
            if not products_by_same_unique_code and not products_by_same_ean_code:
                self._create_new_product(
                    extra_prod_dict, prod_obj, supplier_product_info_dict
                )

            # Otherwise if this is a new supplier, add to existing product
            elif (
                not products_by_same_unique_code
                and products_by_same_ean_code
                and supplier_product_info_dict["partner_id"]
                not in products_by_same_ean_code.mapped("seller_ids.partner_id.id")
            ):
                products_by_same_ean_code[0].write(
                    {"seller_ids": [(0, 0, supplier_product_info_dict)]}
                )
            elif products_by_same_unique_code and supplier_product_info_dict[
                "omschrijving"
            ] not in products_by_same_unique_code.mapped("seller_ids.partner_id.id"):
                supplier_product_info_dict["sequence"] = 5  # give it least preference
                products_by_same_unique_code[0].write(
                    {"seller_ids": [(0, 0, supplier_product_info_dict)]}
                )
            # Otherwise throw an error, supplier/eancode already exists
            else:
                raise ValidationError(
                    _(
                        "A Product with same Leveranciernummer& Bestelnummer already imported"  # noqa: E501
                    )
                )
            self.write({"state": "imported"})
        except ValidationError:
            if self.env.context.get("force"):
                pass
            else:
                raise
        return

    def _create_new_product(self, extra_prod_dict, prod_obj, supplier_dict):
        all_fields = self.env["product.template"].fields_get().keys()
        prod_dict = self.env["product.template"].default_get(list(all_fields))
        prod_dict.update(
            {
                "unique_id": self.unique_id,
                "eancode": self.eancode,
                "barcode": self.eancode,
                "name": self.omschrijving,
                "standard_price": self.inkoopprijs,
                "list_price": self.consumentenprijs,
                "seller_ids": [(0, 0, supplier_dict)],
                "kwaliteit": self.kwaliteit,
                "available_in_pos": True,
                "eenheid": self.eenheid,
                "herkomst": self.herkomst,
                "inhoud": self.inhoud,
                "verpakkingce": self.verpakkingce,
                "ingredients": self.ingredienten,
                "usage_tips": self.gebruikstips,
                "storage_temperature": self.bewaartemperatuur,
                "use_by_days": self.aantaldagenhoudbaar,
                "d204": self.d204,
                "d209": self.d209,
                "d210": self.d210,
                "d212": self.d212,
                "d213": self.d213,
                "d214": self.d214,
                "d234": self.d234,
                "d215": self.d215,
                "d239": self.d239,
                "d216": self.d216,
                "d217": self.d217,
                "d217b": self.d217b,
                "d220": self.d220,
                "d221": self.d221,
                "d221b": self.d221b,
                "d222": self.d222,
                "d223": self.d223,
                "d236": self.d236,
                "d235": self.d235,
                "d238": self.d238,
                "d238b": self.d238b,
                "d225": self.d225,
                "d226": self.d226,
                "d228": self.d228,
                "d230": self.d230,
                "d232": self.d232,
                "d237": self.d237,
                "d240": self.d240,
                "d241": self.d241,
                "d242": self.d242,
                "proefdiervrij": self.proefdiervrij,
                "vegetarisch": self.vegetarisch,
                "veganistisch": self.veganistisch,
                "rauwemelk": self.rauwemelk,
            }
        )
        prod_dict.update(extra_prod_dict)
        prod_obj.create(prod_dict)

    def _translate_standard_unit_of_packiging(self, supplier_dict):
        if self.sve:
            supplier_dict["min_qty"] = f"{float(self.sve):.2f}"

    def _create_supplier_load_dict(self):
        supplier_dict = {
            "cwa": True,
            "unique_id": self.unique_id,
            "eancode": self.eancode,
            "weegschaalartikel": self.weegschaalartikel,
            "wichtartikel": self.wichtartikel,
            "pluartikel": self.pluartikel,
            "inhoud": self.inhoud,
            "eenheid": self.eenheid,
            "verpakkingce": self.verpakkingce,
            "merk": self.merk,
            "kwaliteit": self.kwaliteit,
            "btw": self.btw,
            "cblcode": self.cblcode,
            "bestelnummer": self.bestelnummer,
            "leveranciernummer": self.leveranciernummer,
            "proefdiervrij": self.proefdiervrij,
            "vegetarisch": self.vegetarisch,
            "veganistisch": self.veganistisch,
            "rauwemelk": self.rauwemelk,
            "inkoopprijs": self.inkoopprijs,
            "consumentenprijs": self.consumentenprijs,
            "old_consumentenprijs": self.consumentenprijs,
            "ingangsdatum": self.ingangsdatum,
            "herkomst": self.herkomst,
            "ingredients": self.ingredienten,
            "statiegeld": self.statiegeld,
            "omschrijving": self.omschrijving,
            "kassaomschrijving": self.kassaomschrijving,
            "plucode": self.plucode,
            "sve": self.sve,
            "status": self.status,
            "keurmerkbio": self.keurmerkbio,
            "keurmerkoverig": self.keurmerkoverig,
            "herkomstregio": self.herkomstregio,
            "use_by_days": self.aantaldagenhoudbaar,
            "storage_temperature": self.bewaartemperatuur,
            "usage_tips": self.gebruikstips,
            "lengte": self.lengte,
            "breedte": self.breedte,
            "hoogte": self.hoogte,
            "code": self.code,
            "d204": self.d204,
            "d209": self.d209,
            "d210": self.d210,
            "d212": self.d212,
            "d213": self.d213,
            "d214": self.d214,
            "d234": self.d234,
            "d215": self.d215,
            "d239": self.d239,
            "d216": self.d216,
            "d217": self.d217,
            "d217b": self.d217b,
            "d220": self.d220,
            "d221": self.d221,
            "d221b": self.d221b,
            "d222": self.d222,
            "d223": self.d223,
            "d236": self.d236,
            "d235": self.d235,
            "d238": self.d238,
            "d238b": self.d238b,
            "d225": self.d225,
            "d226": self.d226,
            "d228": self.d228,
            "d230": self.d230,
            "d232": self.d232,
            "d237": self.d237,
            "d240": self.d240,
            "d241": self.d241,
            "d242": self.d242,
            "pos_categ_id": self.pos_categ_id,
            "product_code": self.bestelnummer,
            "product_name": self.omschrijving,
            "price": self.inkoopprijs,
            "date_start": self.ingangsdatum,
            "partner_id": self.vendor_id.id,
        }
        return supplier_dict

    def _translate_brand(self, extra_prod_dict):
        brand = self.merk
        translated_brand = self.env["cwa.product.brands"].get_translated(brand)
        if not translated_brand and not self.env.context.get(
            "force"
        ):  # skip this if via force
            raise ValidationError(_("Could not translate brand %s") % (brand,))
        else:
            extra_prod_dict["product_brand_id"] = translated_brand.destination_value.id

    def _translate_uoms(self, extra_prod_dict):
        uom = self.eenheid
        unit_uom_id = self.env["uom.uom"].search(
            [("id", "=", self.env.ref("uom.product_uom_unit").id)]
        )
        override_uom_id_translation = None
        if self.eancode and unit_uom_id:
            override_uom_id_translation = unit_uom_id
        translated_eenheid = self.env["cwa.product.uom"].get_translated(uom)
        if (
            not translated_eenheid and not override_uom_id_translation
        ) and not self.env.context.get("force"):  # skip this if via force
            raise ValidationError(_("Could not translate UoM %s") % (uom,))
        else:
            if override_uom_id_translation:
                extra_prod_dict["uom_id"] = unit_uom_id.id
                extra_prod_dict["uom_po_id"] = unit_uom_id.id
            else:
                extra_prod_dict["uom_id"] = translated_eenheid.uom_id.id
                extra_prod_dict["uom_po_id"] = translated_eenheid.uom_po_id.id

    def _translate_cbl_codes(self, extra_prod_dict):
        cblcode = self.cblcode
        translated_cblcode = self.env["cwa.product.cblcode"].get_translated(cblcode)
        if not translated_cblcode and not self.env.context.get(
            "force"
        ):  # skip this if via force
            msg = _("Cannot translate CBL code %s into product categories.") % (
                self.cblcode,
            )
            raise ValidationError(msg)
        elif not translated_cblcode.internal_category.id:
            msg = _(
                "Cannot translate CBL code %s into internal category."
                "Please change translation in translation model!"
            ) % (self.cblcode,)
            raise IncompleteValidationError(msg)
        else:
            extra_prod_dict["categ_id"] = translated_cblcode.internal_category.id
            extra_prod_dict["pos_categ_id"] = translated_cblcode.pos_category.id

    def _translate_quality(self, extra_prod_dict):
        quality = self.kwaliteit
        if quality:
            translated_quality = self.env["cwa.product.quality"].get_translated(quality)
            if not translated_quality and not self.env.context.get(
                "force"
            ):  # skip this if via force
                raise ValidationError(_("Could not translate Quality %s") % (quality,))
            else:
                extra_prod_dict["kwaliteit"] = translated_quality.id
        else:
            extra_prod_dict["kwaliteit"] = self.env.ref(
                "product_import_cwa.cwa_quality_afbak"
            ).id

    def _translate_product_quality(self, extra_prod_dict):
        quality = self.kwaliteit
        if quality:
            translated_quality = self.env[
                "cwa.product.quality"
            ].get_translated_product_quality(quality)
            if not translated_quality and not self.env.context.get(
                "force"
            ):  # skip this if via force
                raise ValidationError(
                    _("Could not translate Product Quality %s") % (quality,)
                )
            else:
                extra_prod_dict["product_quality_id"] = translated_quality.id

    def _translate_vat(self, extra_prod_dict):
        btw = self.btw
        if btw:
            translated_btw = self.env["cwa.vat.tax"].get_translated(btw)
            if not translated_btw and not self.env.context.get(
                "force"
            ):  # skip this if via force
                raise ValidationError(
                    _("Could not get the tax translation for btw: %s") % (btw,)
                )
            else:
                extra_prod_dict["taxes_id"] = [(6, 0, translated_btw.sale_tax.ids)]
                extra_prod_dict["supplier_taxes_id"] = [
                    (6, 0, translated_btw.purchase_tax.ids)
                ]

    def _translate_product_origin(self, extra_prod_dict):
        country_code = self.herkomst
        if country_code:
            product_origin = self.env["product_food_fields.product_origin"].search(
                [("country_code", "=", country_code)]
            )
            if not product_origin:
                raise ValidationError(
                    _("Could not translate country code %s") % (country_code,)
                )
            else:
                extra_prod_dict["product_origin_id"] = product_origin.id

    @api.depends("leveranciernummer")
    def _compute_vendor_id(self):
        for this in self:
            supplier = (
                self.env["cwa.product.suppliers"]
                .search([("leveranciernummer", "=", this.leveranciernummer)])
                .res_partner_id
            )
            this.vendor_id = supplier.id

    @api.model
    def _search_vendor_id(self, operator, value):
        pass

    def _get_prod_file_from_ftp(self):
        ir_config = self.env["ir.config_parameter"].sudo()
        config_address = tools.config.get("ftp_address", False)
        if ir_config.get_param("cwa_enable_ftp_import", default=False):
            host = ir_config.get_param("cwa_ftp_address")
            username = ir_config.get_param("cwa_ftp_username")
            passwd = ir_config.get_param("cwa_ftp_password")

        else:
            # Get credentials from the odoo.cfg
            host = config_address
            username = tools.config.get("ftp_username")
            passwd = tools.config.get("ftp_password")

        if not host or not username or not passwd:
            return

        tmp = False
        try:
            ftp_server = ftplib.FTP(host, username, passwd, timeout=20)
            ftp_server.encoding = "utf-8"
            root = "VoorWinkel"
            # Go into the Root Directory
            ftp_server.cwd(root)
            files_in_dir = ftp_server.nlst()
            # ignore Actie files
            files_in_dir = [x for x in files_in_dir if "Artikelen" in x]
            # pick the latest if there are files
            if not files_in_dir:
                _logger.error("Directory '%s' is empty!" % root)
                return
            remote = f"/{root}/{files_in_dir[-1]}"
            tmp = "/tmp/products_data.xml"
            with open(tmp, "wb") as file:
                _logger.info(f"Downloading file: {remote} >>>> {tmp}")
                try:
                    ftp_server.retrbinary("RETR %s" % remote, file.write)
                    _logger.info("File successfully downloaded....proceed with Import!")
                except ftplib.error_perm as err:
                    _logger.error("Downloading Failed!!: %s" % err)
                    return

                ftp_server.quit()
        except ftplib.all_errors as err:
            _logger.error("Failed to Download from FTP: %s" % err)
        return tmp
