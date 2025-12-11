odoo.define("dfc_pos_improvements.ProductScreen", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const {onMounted} = owl;

    const CustomProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            setup() {
                super.setup();
                onMounted(async () => {
                    await this._handlePendingBarcode();
                });
            }

            async _handlePendingBarcode() {
                if (this.env.pos.pendingBarcodeResult) {
                    const pendingResult = this.env.pos.pendingBarcodeResult;
                    delete this.env.pos.pendingBarcodeResult;

                    console.debug(
                        "Processing pending barcode from receipt screen:",
                        pendingResult
                    );

                    if (
                        ["product", "price", "weight", "quantity"].includes(
                            pendingResult.type
                        )
                    ) {
                        await this._barcodeProductAction(pendingResult);
                    }
                }
            }
        };

    Registries.Component.extend(ProductScreen, CustomProductScreen);

    return ProductScreen;
});
