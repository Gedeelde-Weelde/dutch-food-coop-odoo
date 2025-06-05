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
                    console.debug('Price check digit rule matched, original price:', code.value);

                    // Modify the price: set the highest digit to zero
                    const originalPrice = code.value;
                    const modifiedPrice = this._modifyPriceCheckDigit(originalPrice);

                    console.debug('Modified price:', modifiedPrice);

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

                // Find the highest digit
                let highestDigit = '0';
                let highestIndex = -1;

                for (let i = 0; i < priceStr.length; i++) {
                    const char = priceStr[i];
                    // Only consider numeric digits
                    if (/\d/.test(char) && char > highestDigit) {
                        highestDigit = char;
                        highestIndex = i;
                    }
                }

                // If we found a digit to replace
                if (highestIndex !== -1) {
                    // Replace the highest digit with '0'
                    const modifiedPriceStr = priceStr.substring(0, highestIndex) + '0' + priceStr.substring(highestIndex + 1);
                    return parseFloat(modifiedPriceStr);
                }

                // If no digit found or any error, return original price
                return price;
            }
        };

    Registries.Component.extend(ProductScreen, CustomProductScreen);

    return ProductScreen;
});
