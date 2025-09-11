# POS Payment Logging

This Odoo module adds logging functionality to the Point of Sale (POS) payment screen. It records payment operations in the browser's IndexedDB database.

## Features

- Logs payment operations (add payment, delete payment, validate payment)
- Stores logs in the browser's IndexedDB database
- No server-side storage required
- Minimal impact on POS performance

## Technical Information

### Logged Events

The module logs the following payment events:

1. **Adding a payment line** - When a payment method is selected
2. **Deleting a payment line** - When a payment is removed
3. **Validating payment** - When an order is finalized

### Log Data Structure

Each log entry contains:

- `action`: The type of action (add_payment, delete_payment, validate_payment)
- `payment_method`: Name of the payment method
- `payment_method_id`: ID of the payment method
- `amount`: Payment amount
- `order_uid`: Unique identifier of the order
- `order_name`: Name/reference of the order
- `timestamp`: ISO timestamp of when the action occurred

### Browser Database

The module uses IndexedDB to store logs with the following configuration:
- Database name: `pos_payment_logs`
- Object store: `payment_logs`
- Indexes: `timestamp`, `payment_method`, `amount`

## Usage

The module works automatically after installation. No configuration is needed.

To view the logs, you can use the browser's developer tools:
1. Open the browser's developer console (F12)
2. Go to the "Application" tab
3. Under "Storage", expand "IndexedDB"
4. Select "pos_payment_logs" database
5. View the "payment_logs" object store

## License

This module is licensed under the AGPL-3.0 license.
