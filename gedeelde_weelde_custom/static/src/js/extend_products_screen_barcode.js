odoo.define('gedeelde_weelde_custom.ProductScreen', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const CustomProductScreen = ProductScreen =>
        class extends ProductScreen {
            async _barcodeProductAction(code) {
                console.debug('Barcode product action called with code:', code);

                // Check if this is a price type barcode and if the rule has price_check_digit set
                if (code.type === 'price' && code.rule && code.rule.price_check_digit) {

                    // Modify the price: set the highest digit to zero
                    const originalPrice = code.value;
                    const modifiedPrice = this._modifyPriceCheckDigit(originalPrice);


                    // Create a modified code object with the new price
                    const modifiedCode = Object.assign({}, code, { value: modifiedPrice });

                    // Call the parent method with the modified code
                    return super._barcodeProductAction(modifiedCode);
                }

                // For all other cases, use the original method
                return super._barcodeProductAction(code);
            }

            _modifyPriceCheckDigit(price) {
                // Convert price to string to work with digits
                const priceStr = price.toString();
                const modifiedPriceStr = '0' + priceStr.substring(1);
                return parseFloat(modifiedPriceStr);
            }
        };

    Registries.Component.extend(ProductScreen, CustomProductScreen);

    return ProductScreen;
});
