odoo.define("gedeelde_weelde_custom.ProductScreen", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const { onMounted } = owl;

    const CustomProductScreen = (ProductScreen) =>
        class extends ProductScreen {

            setup() {
                super.setup();
                onMounted(async () => {
                    this._handlePendingBarcode();
                });
            }

            async _handlePendingBarcode() {
                if (this.env.pos.pendingBarcodeResult) {
                    const pendingResult = this.env.pos.pendingBarcodeResult;
                    delete this.env.pos.pendingBarcodeResult; // Clear it

                    console.debug('Processing pending barcode from receipt screen:', pendingResult);

                    // Process the barcode using the appropriate action
                    if (pendingResult.type === 'product') {
                        await this._barcodeProductAction(pendingResult);
                    } else if (pendingResult.type === 'price') {
                        await this._barcodeProductAction(pendingResult);
                    } else if (pendingResult.type === 'weight') {
                        await this._barcodeProductAction(pendingResult);
                    } else if (pendingResult.type === 'quantity') {
                        await this._barcodeProductAction(pendingResult);
                    }
                }
            }

            async _barcodeProductAction(code) {
                console.debug("Barcode product action called with code:", code);

                // Check if this is a price type barcode and if the rule has price_check_digit set
                if (code.type === "price" && code.rule && code.rule.price_check_digit) {
                    const originalPrice = code.value;
                    const modifiedPrice = this._modifyPriceCheckDigit(originalPrice);

                    // Create a modified code object with the new price
                    const modifiedCode = Object.assign({}, code, {
                        value: modifiedPrice,
                    });

                    // Call the parent method with the modified code
                    return super._barcodeProductAction(modifiedCode);
                }

                // For all other cases, use the original method
                return super._barcodeProductAction(code);
            }

            _modifyPriceCheckDigit(price) {
                // If the price is less than 100, this means that the price check digit was 0.
                // In that case we don't have to do anything.
                if (price < 100) {
                    return price;
                }
                const priceStr = price.toString();
                const modifiedPriceStr = "0" + priceStr.substring(1);
                return parseFloat(modifiedPriceStr);
            }
        };

    Registries.Component.extend(ProductScreen, CustomProductScreen);

    return ProductScreen;
});
