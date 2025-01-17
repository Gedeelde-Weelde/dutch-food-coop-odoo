import logging

from odoo import fields, models

from .utils import PRESENCE_SELECTION, YESNO_SELECTION

_logger = logging.getLogger(__name__)


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    sequence = fields.Integer(default=1)
    cwa = fields.Boolean(string="Is Cwa")
    unique_id = fields.Char(index=True)
    eancode = fields.Char(help="EAN code.")
    weegschaalartikel = fields.Boolean()
    wichtartikel = fields.Boolean()
    pluartikel = fields.Boolean()
    inhoud = fields.Char(help="Inhoud van de verpakking.")
    eenheid = fields.Char(help="Eenheid van de inhoud.")
    verpakkingce = fields.Char(help="Verpakking van consumenteneenheid.")
    merk = fields.Char(help="Merk.")
    kwaliteit = fields.Char(help="Kwaliteitsaanduiding.")
    btw = fields.Char(help="BTW percentage 0, 6 of 21.")
    cblcode = fields.Char(help="Cblcode.")
    leveranciernummer = fields.Char(help="Nummer van de leverancier.")
    bestelnummer = fields.Char(help="Bestelnummer van artikel bij leverancier.")
    proefdiervrij = fields.Selection(YESNO_SELECTION)
    vegetarisch = fields.Selection(YESNO_SELECTION)
    veganistisch = fields.Selection(YESNO_SELECTION)
    rauwemelk = fields.Selection(YESNO_SELECTION)
    inkoopprijs = fields.Float(help="Inkoopprijs.")
    consumentenprijs = fields.Float("Adviesprijs", help="Adviesprijs.")
    old_consumentenprijs = fields.Float("Old Adviesprijs", help="Old Adviesprijs.")
    ingangsdatum = fields.Date(help="Ingangsdatum van product.")
    ## TODO: doubles origin field in product_food_fields
    herkomst = fields.Char(help="Land van herkomst in vorm ISO 3166 code.")
    statiegeld = fields.Float(help="Statiegeldbedrag.")
    omschrijving = fields.Char(help="Omschrijving van het product.")
    kassaomschrijving = fields.Char(
        help="Korte omschrijving van het product tbv de kassa."
    )
    plucode = fields.Char(help="4-cijferige plucode.")
    sve = fields.Char(help="Standaard verpakkingseenheid bij leverancier.")
    status = fields.Char(help="Mogelijke waarden: Actief/Non Actief/Gesaneerd.")
    keurmerkbio = fields.Char(help="Keurmerkbio.")
    keurmerkoverig = fields.Char(help="Keurmerkoverig.")
    herkomstregio = fields.Char(help="Regio van herkomst.")
    lengte = fields.Char(help="Lengte.")
    breedte = fields.Char(help="Breedte.")
    hoogte = fields.Char(help="Hoogte.")
    code = fields.Char(help="Code.")
    d204 = fields.Selection(PRESENCE_SELECTION, help="Cacao.")
    d209 = fields.Selection(PRESENCE_SELECTION, help="Glutamaat.")
    d210 = fields.Selection(PRESENCE_SELECTION, help="Gluten.")
    d212 = fields.Selection(PRESENCE_SELECTION, help="Ei.")
    d213 = fields.Selection(PRESENCE_SELECTION, help="Kip.")
    d214 = fields.Selection(PRESENCE_SELECTION, help="Melk.")
    d234 = fields.Selection(PRESENCE_SELECTION, help="Koriander.")
    d215 = fields.Selection(PRESENCE_SELECTION, help="Lactose.")
    d239 = fields.Selection(PRESENCE_SELECTION, help="Lupine.")
    d216 = fields.Selection(PRESENCE_SELECTION, help="Mais.")
    d217 = fields.Selection(PRESENCE_SELECTION, help="Noten.")
    d217b = fields.Selection(PRESENCE_SELECTION, help="Notenolie.")
    d220 = fields.Selection(PRESENCE_SELECTION, help="Peulvruchten.")
    d221 = fields.Selection(PRESENCE_SELECTION, help="Pinda.")
    d221b = fields.Selection(PRESENCE_SELECTION, help="Pindaolie.")
    d222 = fields.Selection(PRESENCE_SELECTION, help="Rogge.")
    d223 = fields.Selection(PRESENCE_SELECTION, help="Rundvlees.")
    d236 = fields.Selection(PRESENCE_SELECTION, help="Schaaldieren.")
    d235 = fields.Selection(PRESENCE_SELECTION, help="Selderij.")
    d238 = fields.Selection(PRESENCE_SELECTION, help="Sesam.")
    d238b = fields.Selection(PRESENCE_SELECTION, help="Sesamolie.")
    d225 = fields.Selection(PRESENCE_SELECTION, help="Soja.")
    d226 = fields.Selection(PRESENCE_SELECTION, help="Soja-olie.")
    d228 = fields.Selection(PRESENCE_SELECTION, help="Sulfiet.")
    d230 = fields.Selection(PRESENCE_SELECTION, help="Tarwe.")
    d232 = fields.Selection(PRESENCE_SELECTION, help="Varkensvlees.")
    d237 = fields.Selection(PRESENCE_SELECTION, help="Vis.")
    d240 = fields.Selection(PRESENCE_SELECTION, help="Wortel.")
    d241 = fields.Selection(PRESENCE_SELECTION, help="Mosterd.")
    d242 = fields.Selection(PRESENCE_SELECTION, help="Weekdieren.")
    pos_categ_id = fields.Char(
        "NOT A REFERENCE", help="Not a reference field, just a char field."
    )
    has_new_price = fields.Boolean(string="Has new price")
    product_price = fields.Float(
        related="product_tmpl_id.standard_price", string="Current Price"
    )

    def compare_prices(self):
        recs = self.search([("cwa", "=", True)])
        cwa_obj = self.env["cwa.product"]
        for this in recs:
            cwa = cwa_obj.search([("unique_id", "=", this.unique_id)])
            if cwa and this.price != cwa[0].inkoopprijs:
                this.write(
                    {
                        "has_new_price": True,
                        "price": cwa[0].inkoopprijs,
                        "inkoopprijs": cwa[0].inkoopprijs,
                        "consumentenprijs": cwa[0].consumentenprijs,
                    }
                )
                this.product_tmpl_id.has_new_price = True
            if cwa:
                cwa[0].write({"state": "imported"})
        cwa_all = cwa_obj.search([("state", "=", "imported")])
        already_imported = cwa_obj.search(
            [("unique_id", "in", recs.mapped("unique_id"))]
        )
        # Get ones with state imported but not in supplier info
        not_imported = cwa_all - already_imported
        for item in not_imported:
            item.write({"state": "new"})

    def update_price(self):
        """Updates the price with new value"""
        for this in self:
            this.product_tmpl_id.write(
                {
                    "standard_price": this.inkoopprijs,
                    "list_price": this.consumentenprijs,
                    "has_new_price": False,
                }
            )
            this.write(
                {
                    "has_new_price": False,
                    "old_consumentenprijs": this.consumentenprijs,
                }
            )
        return True

    def ignore_price_change(self):
        for this in self:
            this.write(
                {
                    "has_new_price": False,
                    "price": this.product_price,
                    "inkoopprijs": this.product_price,
                    "consumentenprijs": this.old_consumentenprijs,
                }
            )
            this.product_tmpl_id.has_new_price = False

    def unlink(self):
        for prod in self:
            cwa = self.env["cwa.product"].search([("unique_id", "=", prod.unique_id)])
            cwa.write(
                {
                    "state": "new",
                }
            )
        return super().unlink()
