odoo.define('gw_connection_coin.ProductScreen', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const GWConnectionCoinProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            _barcodePartnerAction(code) {
                const partner = this.env.pos.db.get_partner_by_barcode(code.code);
                if (partner) {
                    this.showPopup('ConfirmPopup', {
                        title: this.env._t('Contact Scanned'),
                        body: _.str.sprintf(this.env._t('Scanned contact: %s'), partner.name),
                    });
                }
                return super._barcodePartnerAction(code);
            }
        };

    Registries.Component.extend(ProductScreen, GWConnectionCoinProductScreen);

    return ProductScreen;
});
