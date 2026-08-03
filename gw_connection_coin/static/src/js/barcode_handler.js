odoo.define("gw_connection_coin.ProductScreen", function (require) {
    "use strict";

    const DiscountButton = require("pos_discount.DiscountButton");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    const GWConnectionCoinProductScreen = (ProductScreen) =>
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
            async _checkConnectionCoinExpiry(partner) {
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const expiryDate = new Date(partner.x_cc_verleng);
                const endDate = new Date(partner.x_cc_einde);
                expiryDate.setHours(0, 0, 0, 0);

                if (expiryDate < today && !endDate.getTime()) {
                    const { confirmed } = await this.showPopup("ConfirmPopup", {
                        title: this.env._t("Connection Coin has expired"),
                        body: _.str.sprintf(
                            this.env._t(
                                "The Connection Coin of %s has expired on %s and no longer provides a discount. Ask the customer if they want to renew. If not, ask the customer if they want to return the coin"
                            ),
                            partner.name,
                            partner.x_cc_verleng
                        ),
                        confirmText: this.env._t("Mark as returned"),
                        cancelText: this.env._t("Close"),
                    });
                    if (confirmed) {
                        await this.rpc({
                            model: "res.partner",
                            method: "end_connection_coin",
                            args: [[partner.id]],
                            context: this.env.session.user_context,
                        });
                        partner.x_cc_einde = partner.x_cc_verleng;
                    }
                    return false;
                }
                if (endDate.getTime() && endDate < today) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Connection Coin has been terminated"),
                        body: _.str.sprintf(
                            this.env._t(
                                "The Connection Coin of %s has been terminated on %s. Inform the customer about this and ask if they want to return the coin."
                            ),
                            partner.name,
                            luxon.DateTime.fromISO(partner.x_cc_einde).toLocaleString(
                                luxon.DateTime.DATE_FULL
                            )
                        ),
                    });
                    return false;
                }

                const diffDays = Math.ceil(
                    (expiryDate - today) / (1000 * 60 * 60 * 24)
                );
                console.debug("diffDays", diffDays);
                if (diffDays >= 0 && diffDays <= 14) {
                    this.showPopup("ConfirmPopup", {
                        title: this.env._t("Connection Coin expires soon"),
                        body: _.str.sprintf(
                            this.env._t(
                                "The Connection Coin of %s expires on %s. Alert the customer to renew in time."
                            ),
                            partner.name,
                            luxon.DateTime.fromISO(partner.x_cc_verleng).toLocaleString(
                                luxon.DateTime.DATE_FULL
                            )
                        ),
                    });
                }
                return true;
            }
            async _barcodePartnerAction(code) {
                const partner = this.env.pos.db.get_partner_by_barcode(code.code);
                if (!partner) {
                    return super._barcodePartnerAction(code);
                }

                const isConnectionCoinValid = await this._checkConnectionCoinExpiry(partner);
                console.debug("isConnectionCoinValid", isConnectionCoinValid);
                if (isConnectionCoinValid) {
                    const order = this.env.pos.get_order();
                    order.set_partner(partner);
                    this._applyDiscount();
                }
                return super._barcodePartnerAction(code);
            }
        };

    Registries.Component.extend(ProductScreen, GWConnectionCoinProductScreen);

    return ProductScreen;
});
