from odoo import api, fields, models, _
from odoo.tools import get_barcode_check_digit
from datetime import date
import calendar

class ConnectionCoinWizard(models.TransientModel):
    _name = 'connection.coin.wizard'
    _description = 'Connection Coin Registration Wizard'

    firstname = fields.Char(string="First Name", required=True)
    lastname = fields.Char(string="Last Name", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone Number")
    street = fields.Char(string="Street")
    zip = fields.Char(string="ZIP")
    city = fields.Char(string="City")
    country_id = fields.Many2one('res.country', string="Country")
    date_issuance = fields.Date(string="Date of Issuance", default=fields.Date.context_today, required=True)
    coin_number = fields.Char(string="Coin Number", required=True)
    barcode = fields.Char(string="Barcode")
    bank_account_number = fields.Char(string="Bank Account Number")
    automatic_debit = fields.Boolean(string="Automatische incasso")

    partner_id = fields.Many2one('res.partner', string="Existing Person", help="Find an existing person if available")

    @api.onchange('coin_number')
    def _onchange_coin_number(self):
        if self.coin_number:
            try:
                # Ensure it's numeric and format to 5 digits
                coin_int = int(self.coin_number)
                coin_padded = str(coin_int).zfill(5)
                # First 3: 042, then 5 digits coin, then 4 zeros = 12 digits
                base_barcode = f"042{coin_padded}0000"
                check_digit = get_barcode_check_digit(base_barcode)
                self.barcode = f"{base_barcode}{check_digit}"
            except (ValueError, TypeError):
                # If not numeric, we can't generate a valid barcode this way
                pass

    @api.onchange('firstname', 'lastname')
    def _onchange_name(self):
        if self.firstname and self.lastname:
            name = f"{self.firstname} {self.lastname}"
            partner = self.env['res.partner'].search([('name', 'ilike', name)], limit=1)
            if partner:
                self.partner_id = partner
                self.email = partner.email
                self.phone = partner.phone
                self.street = partner.street
                self.zip = partner.zip
                self.city = partner.city
                self.country_id = partner.country_id
                self.automatic_debit = partner.x_automatic_debit
                if not self.bank_account_number and partner.bank_ids:
                    self.bank_account_number = partner.bank_ids[0].acc_number

    def action_save(self):
        self.ensure_one()

        partner_vals = {
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
            'phone': self.phone,
            'street': self.street,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
            'x_cc_nummer': self.coin_number,
            'x_cc_verleng': self.date_issuance,
            'barcode': self.barcode,
            'x_automatic_debit': self.automatic_debit,
        }

        if self.partner_id:
            self.partner_id.write(partner_vals)
            partner = self.partner_id
        else:
            partner = self.env['res.partner'].create(partner_vals)

        # Update bank account if provided
        if self.bank_account_number:
            existing_bank = self.env['res.partner.bank'].search([
                ('partner_id', '=', partner.id),
                ('acc_number', '=', self.bank_account_number)
            ], limit=1)
            if not existing_bank:
                self.env['res.partner.bank'].create({
                    'acc_number': self.bank_account_number,
                    'partner_id': partner.id,
                })

        # Create Invoice
        self._create_invoice(partner)

        return self.env.ref('gw_connection_coin.action_report_connection_coin_registration').report_action(self)

    def _create_invoice(self, partner):
        today = self.date_issuance or date.today()
        year = today.year

        # Calculate days left in the year (including today)
        total_days_year = 366 if calendar.isleap(year) else 365
        last_day_year = date(year, 12, 31)
        days_left = (last_day_year - today).days + 1

        amount = (days_left / total_days_year) * 110.0

        # Create the invoice
        # Note: We need a product or at least an account.
        # Since I don't know the specific product, I will look for a 'Connection Coin' product or use a generic one.
        product = self.env['product.product'].search([('name', 'ilike', 'Connection Coin')], limit=1)

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': today,
            'invoice_line_ids': [(0, 0, {
                'name': _('Connection Coin Fee'),
                'quantity': 1,
                'price_unit': amount,
                'product_id': product.id if product else False,
            })],
        }

        invoice = self.env['account.move'].create(invoice_vals)
        return invoice
