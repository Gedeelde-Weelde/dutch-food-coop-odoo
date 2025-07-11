odoo.define('gedeelde_weelde_custom.ReceiptScreen', function (require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    const { useBarcodeReader } = require('point_of_sale.custom_hooks');

    const CustomReceiptScreen = (ReceiptScreen) => class extends ReceiptScreen {

        setup() {
            super.setup();

            // Use the proper barcode reader hook
            useBarcodeReader({
                product: this._onBarcodeScanned,
                price: this._onBarcodeScanned,
                weight: this._onBarcodeScanned,
                quantity: this._onBarcodeScanned,
            });
        }

        async _onBarcodeScanned(parsed_result) {
            console.debug('Barcode scanned on receipt screen:', parsed_result);
            this.orderDone();
            // Create a new order and navigate to ProductScreen
            // this._addNewOrder();
            // this.showScreen('ProductScreen');
            //
            // // Optional: Show a brief notification
            // this.showNotification(this.env._t('New order started'));
        }
    };

    Registries.Component.extend(ReceiptScreen, CustomReceiptScreen);

    return ReceiptScreen;
});
