from odoo import fields, models


class CwaDepositWizard(models.TransientModel):
    _name = "cwa.deposit.wizard"
    _description = "CWA Deposit Wizard"

    deposit_price = fields.Float(
        required=True,
        default=lambda self: self.env.context.get("default_deposit_price"),
    )
    target_deposit_product_id = fields.Many2one(
        "product.template", string="Target Deposit Product", required=True
    )

    def action_apply(self):
        self.ensure_one()
        self.env["cwa.product.deposit"].create(
            {
                "source_deposit_price": self.deposit_price,
                "deposit_product_id": self.target_deposit_product_id.id,
            }
        )
