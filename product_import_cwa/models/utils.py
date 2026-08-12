import hashlib
import logging
import math
import re

from lxml import etree

_logger = logging.getLogger(__name__)

PRESENCE_SELECTION = [
    ("0", "ONBEKEND"),
    ("1", "AANWEZIG"),
    ("2", "NIET AANWEZIG"),
    ("3", "MOGELIJK AANWEZIG"),
]

YESNO_SELECTION = [("0", "ONBEKEND"), ("1", "JA"), ("2", "NEE")]

BOOLEAN_KEYS = ("weegschaalartikel", "pluartikel", "wichtartikel")


def ean_checksum(eancode):
    """
    Returns the checksum of an ean string of length 13
    Returns -1 if the string has the wrong length
    """
    if len(eancode) != 13:
        return -1
    oddsum = 0
    evensum = 0
    total = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:  # noqa E722
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def sanitize_ean13(ean13):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean13:
        return "0000000000000"
    ean13 = re.sub("[A-Za-z]", "0", ean13)
    ean13 = re.sub("[^0-9]", "", ean13)
    ean13 = ean13[:13]
    if len(ean13) < 13:
        ean13 = ean13 + "0" * (13 - len(ean13))
    return ean13[:-1] + str(ean_checksum(ean13))


def split_data(data, split_size=50):
    return [data[x : x + split_size] for x in range(0, len(data), split_size)]


def set_external_id(data):
    if data["eancode"] == 0:
        return f"product_ex_id_{data['leveranciernummer']}_{data['bestelnummer']}"
    else:
        return f"product_ex_id_{data['eancode']}"


# Which fields to load from XML
FIELDS_TO_LOAD = (
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
    (None, "unique_id"),
    (None, "hash"),
)


class XMLProductLoader:
    def __init__(self, cwa_product_model):
        self.cwa_product_model = cwa_product_model

        self.cur_unique_ids = set()
        self.new_unique_ids = set()
        self.hash_dict = {}

        self.load_values = []
        self.update_records = []
        self.load_fields = []
        self.load_tags = []

    @staticmethod
    def detect_encoding(xml_file):
        with open(xml_file, "rb") as file:
            # Read the first 1024 bytes to catch the encoding declaration
            first_part = file.read(1024).decode("ascii", errors="ignore")
        match = re.search(r'encoding="(.+?)"', first_part)
        if match:
            return match.group(1)
        return "UTF-8"  # Default encoding if none is specified

    def parse_from_xml(self, prod_file):
        # make a dict with existing products by unique_id
        self.fill_unique_ids_and_hash_dict()
        _logger.debug("Start parsing XML file: %s", prod_file)

        # determine allowed source tags
        # determine list of destination fields
        self.determine_allowed_source_tags_and_destination_fields()

        encoding = self.detect_encoding(prod_file)
        parser = etree.XMLParser(recover=True, encoding=encoding)

        try:
            root = etree.parse(prod_file, parser)
        except etree.XMLSyntaxError:
            _logger.info("Error decoding. Retrying using recover mode...")
            with open(prod_file, "rb") as file:
                file_content = file.read()
            parser = etree.XMLParser(recover=True)
            root = etree.fromstring(file_content, parser)

        _logger.debug("Start iterartion: %s", prod_file)
        for product in root.iter("product"):
            # copy full XML record to dict
            temp_dict = self.copy_record_to_temp_dict(product)

            # decide which ones to load
            load_dict = self.determine_tags_to_load(temp_dict)

            new_hash = self.create_hash_from_recs_to_load(load_dict)

            load_dict["hash"] = new_hash

            # create the unique id for this record
            unique_id = self.create_unique_id(temp_dict)

            load_dict["unique_id"] = unique_id
            self.new_unique_ids.add(unique_id)

            self.determine_if_record_should_be_created_updated_or_ignored(
                load_dict, new_hash, unique_id
            )

        _logger.debug("Start finished iteration: %s", prod_file)
        delete_records = self.calculate_records_that_should_be_deleted()

        return self.load_fields, self.load_values, self.update_records, delete_records

    def calculate_records_that_should_be_deleted(self):
        earlier_imported_ids_not_present_in_current_data = list(
            self.cur_unique_ids - self.new_unique_ids
        )
        return earlier_imported_ids_not_present_in_current_data

    def determine_if_record_should_be_created_updated_or_ignored(
        self, load_dict, new_hash, unique_id
    ):
        old_hash = self.hash_dict.get(unique_id, None)
        if old_hash:
            # record exists, update only when hash is different
            if old_hash != new_hash:
                load_dict = self.convert_booleans_in_load_dict(load_dict)
                self.update_records.append(load_dict)
        else:
            # convert load_dict to a list and append to load_values
            load_list = [load_dict.get(name, None) for name in self.load_fields]
            self.load_values.append(load_list)

    def create_unique_id(self, temp_dict):
        return f"{temp_dict['leveranciernummer']}-{temp_dict['bestelnummer']}"

    def create_hash_from_recs_to_load(self, load_dict):
        # create a hash from the recs to load
        _hash = hashlib.md5()
        for key, value in load_dict.items():
            _hash.update(key.encode("utf-8"))
            _hash.update(str(value).encode("utf-8"))
        new_hash = _hash.hexdigest()
        return new_hash

    def determine_tags_to_load(self, temp_dict):
        load_dict = {}
        for tag, value in temp_dict.items():
            if tag not in self.load_tags:
                _logger.warning("Ignoring unknown tag: %s", tag)
                continue

            # load prices as floats
            elif tag in ("consumentenprijs", "inkoopprijs"):
                load_dict[tag] = f"{float(value):.2f}"

            elif tag == "verpakkingce":
                if value:
                    load_dict[tag] = value.upper()
                # else:
                #     load_dict[tag] = 'STUKS'

            # load yes/no selections
            elif tag in (
                "proefdiervrij",
                "vegetarisch",
                "veganistisch",
                "rauwemelk",
            ):
                if value in ["0", "1", "2"]:
                    load_dict[tag] = value
                else:
                    load_dict[tag] = "0"

            # load booleans
            elif tag in BOOLEAN_KEYS:
                if value == "1":
                    load_dict[tag] = "true"
                else:
                    load_dict[tag] = "false"

            elif tag == "omschrijving":
                load_dict[tag] = value.upper()

            elif tag == "ingredienten":
                load_dict[tag] = (
                    value.replace("Ingredienten: ", "")
                    if isinstance(value, str)
                    else value
                )

            else:
                load_dict[tag] = value.upper() if value else None
        return load_dict

    def copy_record_to_temp_dict(self, product):
        temp_dict = {}
        for item in product:
            temp_dict[item.tag] = item.text if item.text else None
        return temp_dict

    def determine_allowed_source_tags_and_destination_fields(self):
        for rec in FIELDS_TO_LOAD:
            if isinstance(rec, tuple):
                if rec[0]:
                    self.load_tags.append(rec[0])
                if rec[1]:
                    self.load_fields.append(rec[1])
            else:
                self.load_tags.append(rec)
                self.load_fields.append(rec)

    def fill_unique_ids_and_hash_dict(self):
        records = self.cwa_product_model.search([]).read(["unique_id", "hash"])
        for record in records:
            self.cur_unique_ids.add(record["unique_id"])
            self.hash_dict[record["unique_id"]] = record["hash"]

    def convert_booleans_in_load_dict(self, load_dict):
        return_dict = {}
        for key, value in load_dict.items():
            if key in BOOLEAN_KEYS:
                if value == "true":
                    return_dict[key] = True
                else:
                    return_dict[key] = False
            else:
                return_dict[key] = value
        return return_dict
