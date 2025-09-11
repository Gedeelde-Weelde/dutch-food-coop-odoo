# POS Order Logging

This Odoo module adds comprehensive logging functionality to the Point of Sale (POS) system.
It records order operations, payment events, and system events in the browser's IndexedDB database.

## Features

- Logs complete order lifecycle (creation, product changes, payment, completion)
- Logs payment operations (add payment, delete payment, validate payment)
- Logs order state transitions and screen navigation
- Captures errors and system events
- Stores logs in the browser's IndexedDB database
- Export logs as CSV files for analysis
- No server-side storage required
- Minimal impact on POS performance

## Technical Information

### Logged Events

The module logs the following events:

#### Product Screen Events
1. **Order creation** - When a new order is started
2. **Product addition** - When a product is added to the order
3. **Product removal** - When a product is removed from the order
4. **Quantity changes** - When product quantity is modified
5. **Order cancellation** - When an order is discarded
6. **Payment transition** - When moving from product screen to payment screen

#### Payment Screen Events
7. **Adding a payment line** - When a payment method is selected
8. **Deleting a payment line** - When a payment is removed
9. **Validating payment** - When payment is finalized

#### Receipt Screen Events
10. **Order completion** - When an order is successfully completed
11. **Receipt printing** - When a receipt is printed
12. **Next order** - When moving to a new order

#### System Events
13. **Session events** - POS session start/end
14. **Error events** - Failed operations and exceptions

### Log Data Structure

#### Payment Logs
Each payment log entry contains:
- `action`: The type of action (add_payment, delete_payment, validate_payment)
- `payment_method`: Name of the payment method
- `payment_method_id`: ID of the payment method
- `amount`: Payment amount
- `order_uid`: Unique identifier of the order
- `order_name`: Name/reference of the order
- `timestamp`: ISO timestamp of when the action occurred

#### Order Logs
Each order log entry contains:
- `action`: The type of action (new_order, add_product, remove_product, etc.)
- `screen`: The screen where the action occurred (ProductScreen, PaymentScreen, ReceiptScreen)
- `order_uid`: Unique identifier of the order
- `order_name`: Name/reference of the order
- `timestamp`: ISO timestamp of when the action occurred

Additional fields depending on the action type:
- Product actions: `product_id`, `product_name`, `quantity`
- Payment actions: `total_amount`, `payment_methods`
- Error events: `error_type`, `error_message`

### Browser Database

The module uses IndexedDB to store logs with the following configuration:

#### Payment Logs
- Database name: `pos_payment_logs`
- Object store: `payment_logs`
- Indexes: `timestamp`, `payment_method`, `amount`

#### Order Logs
- Database name: `pos_order_logs`
- Object store: `order_logs`
- Indexes: `timestamp`, `order_uid`, `action`, `screen`

## Usage

The module works automatically after installation. No configuration is needed.

To view the logs, you can use the browser's developer tools:

### Viewing Payment Logs
1. Open the browser's developer console (F12)
2. Go to the "Application" tab
3. Under "Storage", expand "IndexedDB"
4. Select "pos_payment_logs" database
5. View the "payment_logs" object store

### Viewing Order Logs
1. Open the browser's developer console (F12)
2. Go to the "Application" tab
3. Under "Storage", expand "IndexedDB"
4. Select "pos_order_logs" database
5. View the "order_logs" object store

You can use the IndexedDB browser interface to filter logs by various indexes such as timestamp, order_uid, action, or screen.

### Exporting Logs as CSV
To export logs for analysis:
1. Open the POS interface
2. On the Product Screen, click the "Export Logs" button in the control panel
3. Two CSV files will be downloaded automatically:
   - `payment_logs_YYYY-MM-DD.csv` - Contains all payment logs
   - `order_logs_YYYY-MM-DD.csv` - Contains all order logs
4. The CSV files can be opened in any spreadsheet application (Excel, Google Sheets, etc.)
5. Each CSV file includes all fields from the logs, with headers in the first row

## License

This module is licensed under the AGPL-3.0 license.
