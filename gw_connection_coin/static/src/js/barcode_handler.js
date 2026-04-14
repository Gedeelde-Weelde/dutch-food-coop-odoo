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
                    console.log('Scanned contact met discount:', partner);
                    console.log('Einde:', partner.x_cc_einde)
                    this.showPopup('ConfirmPopup', {
                        title: this.env._t('Contact Scanned'),
                        body: _.str.sprintf(this.env._t('Scanned contact: %s, %s'), partner.name, partner.x_cc_nummer),
                    });
                }
                // Call apply_discount with the ProductScreen as context
                    // since it shares the same this.env and this.showPopup
                DiscountButton.prototype.apply_discount.call(this, this.env.pos.config.discount_pc);
                return super._barcodePartnerAction(code);
            }
        };

    Registries.Component.extend(ProductScreen, GWConnectionCoinProductScreen);

    return ProductScreen;
});
