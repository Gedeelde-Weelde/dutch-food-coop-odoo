odoo.define("gw_connection_coin.PartnerListScreen", function (require) {
    "use strict";

    const PartnerLine = require("point_of_sale.PartnerLine");
    const PartnerListScreen = require("point_of_sale.PartnerListScreen");
    const Registries = require("point_of_sale.Registries");
    const { useListener } = require("@web/core/utils/hooks");
    const ConnectionCoinUtils = require("gw_connection_coin.utils");

    const GWConnectionCoinPartnerLine = (PartnerLine) =>
        class extends PartnerLine {
            get hasConnectionCoin() {
                return Boolean(this.props.partner.x_cc_nummer);
            }
            onClickActivateCoin() {
                this.trigger("activate-connection-coin", { partner: this.props.partner });
            }
        };

    Registries.Component.extend(PartnerLine, GWConnectionCoinPartnerLine);

    const GWConnectionCoinPartnerListScreen = (PartnerListScreen) =>
        class extends PartnerListScreen {
            setup() {
                super.setup();
                useListener("activate-connection-coin", this._onActivateConnectionCoin);
            }
            async _onActivateConnectionCoin(ev) {
                const { partner } = ev.detail;
                await ConnectionCoinUtils.markConnectionCoinForgotten(this, partner);
                const order = this.currentOrder;
                order.set_partner(partner);
                order.updatePricelist(partner);
                await ConnectionCoinUtils.syncConnectionCoinDiscount(this, partner);
                this.props.resolve({ confirmed: false, payload: false });
                this.trigger("close-temp-screen");
            }
        };

    Registries.Component.extend(PartnerListScreen, GWConnectionCoinPartnerListScreen);

    return PartnerListScreen;
});