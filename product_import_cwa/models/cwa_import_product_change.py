from odoo import api, fields, models

FIELDS_TO_COMPARE = ("ingredients",)


class CwaImportProductChange(models.Model):
    _name = "cwa.import.product.change"
    _description = "CWA Import Product Change"

    state = fields.Selection(
        [
            ("new", "New"),
            ("no-preferred-new", "Non preferred new"),
            ("processed", "Processed"),
        ],
        default="new",
        required=True,
    )
    eancode = fields.Char(store=False, related="source_cwa_product_id.eancode")
    value_changes = fields.Json()
    changed_fields = fields.Char(store=False, compute="_compute_changed_fields")

    affected_product_id = fields.Many2one(
        "product.template", string="Affected Product", required=True, ondelete="cascade"
    )
    source_cwa_product_id = fields.Many2one(
        "cwa.product", string="Source cwa product", required=True, ondelete="cascade"
    )
    product_supplierinfo_id = fields.Many2one(
        "product.supplierinfo",
        compute="_compute_product_supplierinfo",
        search="_search_product_supplierinfo",
        stored=False,
    )

    product_supplierinfo_ingredients = fields.Text(
        related="product_supplierinfo_id.ingredients"
    )
    affected_product_id_ingredients = fields.Text(
        related="affected_product_id.ingredients"
    )
    affected_product_id_list_price = fields.Float(
        string="Current List Price",
        compute="_compute_affected_product_id_list_price",
        inverse="_inverse_set_affected_product_id_list_price",
        store=True,
    )
    affected_product_id_cost_price = fields.Float(
        string="Current Cost Price",
        compute="_compute_affected_product_id_cost_price",
        inverse="_inverse_set_affected_product_id_cost_price",
        store=True,
    )
    product_supplierinfo_list_price = fields.Float(
        related="product_supplierinfo_id.consumentenprijs"
    )
    product_supplierinfo_cost_price = fields.Float(
        related="product_supplierinfo_id.inkoopprijs"
    )
    product_supplierinfo_supplier = fields.Many2one(
        related="product_supplierinfo_id.partner_id",
        store=True,
        readonly=True,
    )

    @api.depends("value_changes")
    def _compute_changed_fields(self):
        for record in self:
            if record.value_changes:
                record.changed_fields = ", ".join(record.value_changes.keys())
            else:
                record.changed_fields = ""

    @api.depends("affected_product_id.list_price")
    def _compute_affected_product_id_list_price(self):
        for record in self:
            record.affected_product_id_list_price = (
                record.affected_product_id.list_price
            )

    def _inverse_set_affected_product_id_list_price(self):
        for record in self:
            if record.affected_product_id:
                record.affected_product_id.list_price = (
                    record.affected_product_id_list_price
                )

    @api.depends("affected_product_id.standard_price")
    def _compute_affected_product_id_cost_price(self):
        for record in self:
            record.affected_product_id_cost_price = (
                record.affected_product_id.standard_price
            )

    def _inverse_set_affected_product_id_cost_price(self):
        for record in self:
            if record.affected_product_id:
                record.affected_product_id.standard_price = (
                    record.affected_product_id_cost_price
                )

    @api.depends("source_cwa_product_id")
    def _compute_product_supplierinfo(self):
        for record in self:
            if record.source_cwa_product_id:
                supplier_info = self.env["product.supplierinfo"].search(
                    [("unique_id", "=", record.source_cwa_product_id.unique_id)],
                    limit=1,
                )
                record.product_supplierinfo_id = (
                    supplier_info.id if supplier_info else False
                )
            else:
                record.product_supplierinfo_id = False

    def _search_product_supplierinfo(self, operator, value):
        product_ids = []  # List to accumulate product IDs matching the search criteria

        if self.source_cwa_product_id:
            supplier_info = self.env["product.supplierinfo"].search(
                [("unique_id", "=", self.source_cwa_product_id.unique_id)],
                limit=1,
            )
            if supplier_info:
                product_ids = [supplier_info.id]

        # Craft a domain that links back to the desired records
        domain = [("id", "in", product_ids)]
        return domain

    @api.model
    def open_form_view(self, record_id):
        if isinstance(record_id, list):
            record_id = record_id[0]  # Take the first id if a list is provided
        return {
            "type": "ir.actions.act_window",
            "name": "Open Form",
            "view_mode": "form",
            "res_model": "cwa.import.product.change",
            "res_id": record_id,
            "view_id": self.env.ref(
                "product_import_cwa.view_cwa_import_product_change_form"
            ).id,
            "target": "new",
        }
