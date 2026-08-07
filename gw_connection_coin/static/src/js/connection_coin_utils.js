odoo.define("gw_connection_coin.utils", function (require) {
    "use strict";

    const DiscountButton = require("pos_discount.DiscountButton");

    // Shared connection-coin discount logic used by both the ProductScreen
    // (barcode scan path) and the PartnerListScreen (manual activation
    // button). Every function takes the calling PosComponent instance as
    // `component` so it can reuse component.env / showPopup / rpc.

    function getDiscountProductId(component) {
        return (
            component.env.pos.config.discount_product_id &&
            component.env.pos.config.discount_product_id[0]
        );
    }

    function applyDiscount(component) {
        const discountProductId = getDiscountProductId(component);
        if (!discountProductId) {
            return;
        }
        const order = component.env.pos.get_order();
        const selectedLine = order.get_selected_orderline();
        const currentMode = component.env.pos.numpadMode;
        DiscountButton.prototype.apply_discount.call(
            component,
            component.env.pos.config.discount_pc
        );
        if (selectedLine && selectedLine.product.id !== discountProductId) {
            order.select_orderline(selectedLine);
            if (component.env.pos.numpadMode !== currentMode) {
                component.env.pos.numpadMode = currentMode;
            }
        }
    }

    function clearDiscount(component) {
        if (!getDiscountProductId(component)) {
            return;
        }
        DiscountButton.prototype.apply_discount.call(component, 0);
    }

    async function checkConnectionCoinExpiry(component, partner) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const expiryDate = new Date(partner.x_cc_verleng);
        const endDate = new Date(partner.x_cc_einde);
        expiryDate.setHours(0, 0, 0, 0);

        if (expiryDate < today && !endDate.getTime()) {
            const { confirmed } = await component.showPopup("ConfirmPopup", {
                title: component.env._t("Connection Coin has expired"),
                body: _.str.sprintf(
                    component.env._t(
                        "The Connection Coin of %s has expired on %s and no longer provides a discount. Ask the customer if they want to renew. If not, ask the customer if they want to return the coin"
                    ),
                    partner.name,
                    partner.x_cc_verleng
                ),
                confirmText: component.env._t("Returned"),
                cancelText: component.env._t("Close"),
            });
            if (confirmed) {
                await component.rpc({
                    model: "res.partner",
                    method: "end_connection_coin",
                    args: [[partner.id]],
                    context: component.env.session.user_context,
                });
                partner.x_cc_einde = partner.x_cc_verleng;
            }
            return false;
        }
        if (endDate.getTime() && endDate < today) {
            component.showPopup("ErrorPopup", {
                title: component.env._t("Connection Coin has been terminated"),
                body: _.str.sprintf(
                    component.env._t(
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

        const diffDays = Math.ceil((expiryDate - today) / (1000 * 60 * 60 * 24));
        if (diffDays >= 0 && diffDays <= 14) {
            const { confirmed } = await component.showPopup("ConfirmPopup", {
                title: component.env._t("Connection Coin expires soon"),
                body: _.str.sprintf(
                    component.env._t(
                        "The Connection Coin of %s expires on %s. Alert the customer to renew in time."
                    ),
                    partner.name,
                    luxon.DateTime.fromISO(partner.x_cc_verleng).toLocaleString(
                        luxon.DateTime.DATE_FULL
                    )
                ),
                confirmText: component.env._t("Stop Coin"),
                cancelText: component.env._t("Close"),
            });
            if (confirmed) {
                await component.rpc({
                    model: "res.partner",
                    method: "end_connection_coin",
                    args: [[partner.id]],
                    context: component.env.session.user_context,
                });
                partner.x_cc_einde = partner.x_cc_verleng;
            }
        }
        return true;
    }

    async function syncConnectionCoinDiscount(component, partner) {
        if (!getDiscountProductId(component)) {
            return;
        }
        if (!partner || !partner.x_cc_nummer) {
            clearDiscount(component);
            return;
        }
        const isValid = await checkConnectionCoinExpiry(component, partner);
        if (isValid) {
            applyDiscount(component);
        } else {
            clearDiscount(component);
        }
    }

    async function markConnectionCoinForgotten(component, partner) {
        const newCount = await component.rpc({
            model: "res.partner",
            method: "mark_connection_coin_forgotten",
            args: [[partner.id]],
            context: component.env.session.user_context,
        });
        partner.x_cc_vergeten = newCount;
        return newCount;
    }

    return {
        getDiscountProductId,
        applyDiscount,
        clearDiscount,
        checkConnectionCoinExpiry,
        syncConnectionCoinDiscount,
        markConnectionCoinForgotten,
    };
});