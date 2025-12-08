import logging

from odoo import api, fields, models

from .utils import (
    PRESENCE_SELECTION,
    YESNO_SELECTION,
)

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    eancode = fields.Char(help="Eancode.")
    kwaliteit = fields.Many2one("cwa.product.quality", help="Kwaliteitsaanduiding.")
    unique_id = fields.Char("Unique ID.", copy=False)

    # From suppliers
    preferred_supplier_id = fields.Many2one(
        "product.supplierinfo",
        compute="_compute_preferred_supplier",
        search="_search_preferred_supplier",
        string="Preferred Supplier",
        store=True,
    )
    inhoud = fields.Char(help="Inhoud van de verpakking.")
    eenheid = fields.Char(help="Eenheid van de inhoud.")
    statiegeld = fields.Float(help="Statiegeldbedrag.")
    herkomst = fields.Char(help="Land van herkomst in vorm ISO 3166 code.")
    proefdiervrij = fields.Selection(YESNO_SELECTION)
    vegetarisch = fields.Selection(YESNO_SELECTION)
    veganistisch = fields.Selection(YESNO_SELECTION)
    rauwemelk = fields.Selection(YESNO_SELECTION)
    plucode = fields.Char(help="4-cijferige plucode.", name="Plucode")
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
    verpakkingce = fields.Char(help="Verpakking van consumenteneenheid.")
    price_per_standard_unit = fields.Float(
        "Price per Standard Unit", compute="_compute_price_per_su"
    )
    margin = fields.Float(compute="_compute_margin", store=False)
    margin_absolute = fields.Float(compute="_compute_margin_absolute", store=False)

    cwa_import_product_changes = fields.One2many(
        "cwa.import.product.change",
        string="CWA Import Product Changes",
        compute="_compute_cwa_import_product_changes",
        copy=False,
        store=False,
    )

    @api.depends("unique_id")
    def _compute_cwa_import_product_changes(self):
        for product in self:
            product_changes = self.env["cwa.import.product.change"].search(
                [("affected_product_id", "=", product.id)]
            )
            product.cwa_import_product_changes = product_changes

    @api.depends("list_price", "standard_price")
    def _compute_margin(self):
        for template in self:
            res = template.taxes_id.compute_all(
                template.list_price, product=template, partner=self.env["res.partner"]
            )
            price_without_taxes = (
                res["total_excluded"] if res["total_excluded"] else template.list_price
            )
            margin = (
                price_without_taxes - template.standard_price
                if price_without_taxes and template.standard_price
                else 0.0
            )
            template.margin = (
                margin / price_without_taxes if price_without_taxes else 0.0
            )

    @api.depends("list_price", "standard_price")
    def _compute_margin_absolute(self):
        for template in self:
            res = template.taxes_id.compute_all(
                template.list_price, product=template, partner=self.env["res.partner"]
            )
            price_without_taxes = (
                res["total_excluded"] if res["total_excluded"] else template.list_price
            )
            template.margin_absolute = (
                price_without_taxes - template.standard_price
                if price_without_taxes and template.standard_price
                else 0.0
            )

    def make_available_in_pos(self):
        for product in self:
            product.write({"available_in_pos": True})

    @api.depends("uom_id", "uom_po_id", "list_price")
    def _compute_price_per_su(self):
        for this in self:
            uom_type = this.uom_id.uom_type
            price = this.list_price
            if this.uom_id != this.uom_po_id:
                if uom_type == "smaller":
                    this.price_per_standard_unit = this.uom_id.factor * price
                elif uom_type == "bigger":
                    this.price_per_standard_unit = this.uom_id.factor_inv * price
                else:
                    this.price_per_standard_unit = this.uom_po_id.factor_inv * price
            else:
                this.price_per_standard_unit = this.list_price

    @api.depends("seller_ids")
    def _compute_preferred_supplier(self):
        for this in self:
            if this.seller_ids:
                preferred_seller = min(this.seller_ids, key=lambda s: s.sequence)
                this.preferred_supplier_id = preferred_seller.id
            else:
                this.preferred_supplier_id = None

    def _search_preferred_supplier(self, operator, value):
        # Search for supplier partners in res.partner
        supplier_domain = [
            ("name", operator, value)
        ]  # Adjust the domain for the search criteria
        matching_partners = self.env["res.partner"].search(supplier_domain)

        if matching_partners:
            supplierinfo_domain = [("partner_id", "in", matching_partners.ids)]
            matching_supplierinfo = self.env["product.supplierinfo"].search(
                supplierinfo_domain
            )
            if matching_supplierinfo:
                return [("preferred_supplier_id", "in", matching_supplierinfo.ids)]

        # If no match is found, return a domain that resolves to no records
        return [("preferred_supplier_id", "=", False)]

    def unlink(self):
        for prod in self:
            for supplier_info in prod.seller_ids:
                cwa = self.env["cwa.product"].search(
                    [("unique_id", "=", supplier_info.unique_id)]
                )
                cwa.write(
                    {
                        "state": "new",
                    }
                )
        return super().unlink()
