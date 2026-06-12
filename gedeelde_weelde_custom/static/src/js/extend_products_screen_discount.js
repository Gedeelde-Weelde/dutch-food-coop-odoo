odoo.define("gw_connection_coin.ProductScreen", function (require) {
    "use strict";

    const DiscountButton = require("pos_discount.DiscountButton");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    const GWDiscountImprovementProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _barcodeProductAction(code) {
                await super._barcodeProductAction(code);
                this._updateDiscount();
            }
            async _addProduct(product, options) {
                await super._addProduct(product, options);
                this._updateDiscount();
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
            _getDiscountProductId() {
                return (
                    this.env.pos.config.discount_product_id &&
                    this.env.pos.config.discount_product_id[0]
                );
            }
            _applyDiscount() {
                const discountProductId = this._getDiscountProductId();
                if (!discountProductId) {
                    return;
                }
                const order = this.env.pos.get_order();
                const selectedLine = order.get_selected_orderline();
                const currentMode = this.env.pos.numpadMode;
                DiscountButton.prototype.apply_discount.call(
                    this,
                    this.env.pos.config.discount_pc
                );
                if (selectedLine && selectedLine.product.id !== discountProductId) {
                    order.select_orderline(selectedLine);
                    if (this.env.pos.numpadMode !== currentMode) {
                        this.env.pos.numpadMode = currentMode;
                    }
                }
            }
            _updateDiscount() {
                const discountProductId = this._getDiscountProductId();
                if (!discountProductId) {
                    return;
                }
                const order = this.env.pos.get_order();
                const discountLine = order
                    .get_orderlines()
                    .find((line) => line.product.id === discountProductId);
                if (discountLine) {
                    this._applyDiscount();
                }
            }
        };

    Registries.Component.extend(ProductScreen, GWDiscountImprovementProductScreen);

    return ProductScreen;
});
