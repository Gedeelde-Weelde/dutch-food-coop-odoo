odoo.define('gw_connection_coin.ProductScreen', function (require) {
    'use strict';

    const DiscountButton = require('pos_discount.DiscountButton');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

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
                if (this.env.pos.numpadMode === 'quantity' || this.env.pos.numpadMode === 'discount' || this.env.pos.numpadMode === 'price') {
                    this._updateDiscount();
                }
            }
            _barcodeDiscountAction(code) {
                super._barcodeDiscountAction(code);
                this._updateDiscount();
            }
            _updateDiscount() {
                const order = this.env.pos.get_order();
                const discountProductId = this.env.pos.config.discount_product_id && this.env.pos.config.discount_product_id[0];
                if (!discountProductId) {
                    return;
                }
                const discountLine = order.get_orderlines().find(line => line.product.id === discountProductId);
                if (discountLine) {
                    const selectedLine = order.get_selected_orderline();
                    const currentMode = this.env.pos.numpadMode;
                    DiscountButton.prototype.apply_discount.call(this, this.env.pos.config.discount_pc);
                    if (selectedLine && selectedLine.product.id !== discountProductId) {
                        order.select_orderline(selectedLine);
                        if (this.env.pos.numpadMode !== currentMode) {
                            this.env.pos.numpadMode = currentMode;
                        }
                    }
                }
            }
            _barcodePartnerAction(code) {
                const partner = this.env.pos.db.get_partner_by_barcode(code.code);
                if (partner) {
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    if (partner.x_cc_einde) {
                        const expiryDate = new Date(partner.x_cc_einde);
                        expiryDate.setHours(0, 0, 0, 0);
                        if (expiryDate < today) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Connection Coin is verlopen'),
                                body: _.str.sprintf(this.env._t('The Connection Coin for %s (Number: %s) expired on %s.'), partner.name, partner.x_cc_nummer, partner.x_cc_einde),
                            });
                            return;
                        }
                        const diffTime = expiryDate - today;
                        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                        if (diffDays >= 0 && diffDays <= 7) {
                            this.showPopup('ConfirmPopup', {
                                title: this.env._t('Connection Coin verlopen'),
                                body: _.str.sprintf(this.env._t('The Connection Coin for %s (Number: %s) will expire in %s days, on %s.'), partner.name, partner.x_cc_nummer, diffDays, partner.x_cc_einde),
                            });
                        }
                    }

                    const order = this.env.pos.get_order();
                    order.set_partner(partner);
                    const discountProductId = this.env.pos.config.discount_product_id && this.env.pos.config.discount_product_id[0];
                    const selectedLine = order.get_selected_orderline();
                    const currentMode = this.env.pos.numpadMode;
                    DiscountButton.prototype.apply_discount.call(this, this.env.pos.config.discount_pc);
                    if (selectedLine && selectedLine.product.id !== discountProductId) {
                        order.select_orderline(selectedLine);
                        if (this.env.pos.numpadMode !== currentMode) {
                            this.env.pos.numpadMode = currentMode;
                        }
                    }
                }
                return super._barcodePartnerAction(code);
            }
        };

    Registries.Component.extend(ProductScreen, GWConnectionCoinProductScreen);

    return ProductScreen;
});
