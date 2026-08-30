odoo.define("gw_connection_coin.ProductScreen", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const ConnectionCoinUtils = require("gw_connection_coin.utils");

    const GWConnectionCoinProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _barcodeProductAction(code) {
                await super._barcodeProductAction(code);
                this._updateDiscount();
            }
            async _addProduct(product, options) {
                if (product.is_connection_coin && !this.env.pos.get_order().partner) {
                    // If no partner is selected, the coin may not be sold.
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("You must select a customer first"),
                        body: _.str.sprintf(
                            this.env._t(
                                "The connection coin product '%s' requires a customer to be selected first."
                            ),
                            product.display_name
                        ),
                    });
                    return;
                }
                await super._addProduct(product, options);
                if (product.is_connection_coin) {
                    ConnectionCoinUtils.applyDiscount(this);
                } else {
                    this._updateDiscount();
                }
            }
            _setValue(val) {
                super._setValue(val);
                if (
                    this.env.pos.numpadMode === "quantity" ||
                    this.env.pos.numpadMode === "discount" ||
                    this.env.pos.numpadMode === "price"
                ) {
                    this._updateDiscount();
                }
            }
            _barcodeDiscountAction(code) {
                super._barcodeDiscountAction(code);
                this._updateDiscount();
            }
            _updateDiscount() {
                const discountProductId =
                    ConnectionCoinUtils.getDiscountProductId(this);
                if (!discountProductId) {
                    return;
                }
                const order = this.env.pos.get_order();
                const discountLine = order
                    .get_orderlines()
                    .find((line) => line.product.id === discountProductId);
                if (discountLine) {
                    ConnectionCoinUtils.applyDiscount(this);
                }
            }
            async _barcodePartnerAction(code) {
                const result = await super._barcodePartnerAction(code);
                const partner = this.env.pos.db.get_partner_by_barcode(code.code);
                if (partner) {
                    await ConnectionCoinUtils.syncConnectionCoinDiscount(this, partner);
                }
                return result;
            }
        };

    Registries.Component.extend(ProductScreen, GWConnectionCoinProductScreen);

    return ProductScreen;
});
