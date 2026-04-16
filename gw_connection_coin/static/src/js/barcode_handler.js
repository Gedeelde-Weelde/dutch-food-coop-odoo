odoo.define('gw_connection_coin.ProductScreen', function (require) {
    'use strict';

    const DiscountButton = require('pos_discount.DiscountButton');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const GWConnectionCoinProductScreen = (ProductScreen) =>
        class extends ProductScreen {
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

                    this.env.pos.get_order().set_partner(partner);
                    // Call apply_discount with the ProductScreen as context
                    // since it shares the same this.env and this.showPopup
                    DiscountButton.prototype.apply_discount.call(this, this.env.pos.config.discount_pc);
                }
                return super._barcodePartnerAction(code);
            }
        };

    Registries.Component.extend(ProductScreen, GWConnectionCoinProductScreen);

    return ProductScreen;
});
