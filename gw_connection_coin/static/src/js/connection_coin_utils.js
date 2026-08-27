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
        // Maintain the current numpad mode after applying the discount.
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

    // Adds the connection coin product for the partner's membership status
    // (member vs non-member) to the current order. Uses order.add_product
    // (the Order model method) rather than a screen component's
    // _addProduct, since this is shared between ProductScreen and
    // PartnerListScreen, which don't share a common UI-level method.
    async function addConnectionCoinRenewalProduct(component, partner) {
        const config = component.env.pos.config;
        const productRef = partner.is_member
            ? config.member_connection_coin_product_id
            : config.non_member_connection_coin_product_id;
        const product =
            productRef && component.env.pos.db.get_product_by_id(productRef[0]);
        if (!product) {
            await component.showPopup("ErrorPopup", {
                title: component.env._t("No connection coin product found"),
                body: component.env._t(
                    "The connection coin product for this partner's membership status is not configured. Set it up in the Point of Sale settings."
                ),
            });
            return;
        }
        component.env.pos.get_order().add_product(product, {});
        applyDiscount(component);
    }

    // Stops the connection coin on the backend, syncs the partner fields on
    // this POS instance to whatever the backend actually wrote (rather than
    // re-deriving the same values client-side), and informs the cashier.
    async function stopConnectionCoin(component, partner) {
        const result = await component.rpc({
            model: "res.partner",
            method: "end_connection_coin",
            args: [[partner.id]],
            context: component.env.session.user_context,
        });
        const newState = result[partner.id];
        partner.cc_end_date = newState.cc_end_date;
        partner.cc_renewal_date = newState.cc_renewal_date;
        await component.showPopup("ConfirmPopup", {
            title: component.env._t("Connection Coin stopped"),
            body: _.str.sprintf(
                component.env._t(
                    "The Connection Coin of %s has been stopped as of %s."
                ),
                partner.name,
                luxon.DateTime.fromISO(newState.cc_end_date).toLocaleString(
                    luxon.DateTime.DATE_FULL
                )
            ),
            confirmText: component.env._t("Ok"),
        });
    }

    // Pure validity check (no popups/RPCs), mirroring the two invalidity
    // conditions in checkConnectionCoinExpiry below. Used where a boolean
    // result is needed synchronously, e.g. to decide whether to show the
    // "activate" button in the partner list.
    function isConnectionCoinValid(partner) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const expiryDate = new Date(partner.cc_renewal_date);
        const endDate = new Date(partner.cc_end_date);
        expiryDate.setHours(0, 0, 0, 0);

        if (expiryDate <= today && !endDate.getTime()) {
            return false;
        }
        if (endDate.getTime() && endDate <= today) {
            return false;
        }
        return true;
    }

    async function checkConnectionCoinExpiry(component, partner) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const expiryDate = new Date(partner.cc_renewal_date);
        const endDate = new Date(partner.cc_end_date);
        expiryDate.setHours(0, 0, 0, 0);

        if (expiryDate <= today && !endDate.getTime()) {
            component.playSound("error");
            const {payload: action} = await component.showPopup("SelectionPopup", {
                title: component.env._t("Connection Coin has expired"),
                body: _.str.sprintf(
                    component.env._t(
                        "The Connection Coin of %s expired on %s and no longer provides a discount. Ask the customer if they want to renew from this date or stop permanently."
                    ),
                    partner.name,
                    luxon.DateTime.fromISO(partner.cc_renewal_date).toLocaleString(
                        luxon.DateTime.DATE_FULL
                    )
                ),
                list: [
                    {
                        id: "renew",
                        label: component.env._t("Renew"),
                        isSelected: false,
                        item: "renew",
                    },
                    {
                        id: "stop",
                        label: component.env._t("Stop Coin"),
                        isSelected: false,
                        item: "stop",
                    },
                    {
                        id: "none",
                        label: component.env._t("Do nothing"),
                        isSelected: false,
                        item: "none",
                    },
                ],
                cancelText: component.env._t("Close"),
            });
            if (action === "stop") {
                await stopConnectionCoin(component, partner);
                return false;
            } else if (action === "renew") {
                // AddConnectionCoinRenewalProduct already applied the
                // discount; reporting valid here stops
                // syncConnectionCoinDiscount from immediately clearing it.
                await addConnectionCoinRenewalProduct(component, partner);
                return true;
            }
            return false;
        }
        if (endDate.getTime() && endDate <= today) {
            component.playSound("error");
            const {payload: action} = await component.showPopup("SelectionPopup", {
                title: component.env._t("Connection Coin has been terminated"),
                body: _.str.sprintf(
                    component.env._t(
                        "The Connection Coin of %s has been terminated on %s. Inform the customer about this and ask if the coin should be activated from today."
                    ),
                    partner.name,
                    luxon.DateTime.fromISO(partner.cc_end_date).toLocaleString(
                        luxon.DateTime.DATE_FULL
                    )
                ),
                list: [
                    {
                        id: "activate",
                        label: component.env._t("Activate"),
                        isSelected: false,
                        item: "activate",
                    },
                    {
                        id: "none",
                        label: component.env._t("Do nothing"),
                        isSelected: false,
                        item: "none",
                    },
                ],
                cancelText: component.env._t("Close"),
            });
            if (action === "activate") {
                // Same reasoning as the "renew" branch above: reporting
                // valid here keeps syncConnectionCoinDiscount from
                // clearing the discount addConnectionCoinRenewalProduct
                // just applied.
                await addConnectionCoinRenewalProduct(component, partner);
                return true;
            }
            return false;
        }

        const daysFromExpiry = Math.ceil((expiryDate - today) / (1000 * 60 * 60 * 24));
        if (daysFromExpiry >= 0 && daysFromExpiry <= 28) {
            component.playSound("error");
            const {payload: action} = await component.showPopup("SelectionPopup", {
                title: component.env._t("Connection Coin expires soon"),
                body: _.str.sprintf(
                    component.env._t(
                        "The Connection Coin of %s expires on %s. Ask the customer if they want to renew or stop from this date."
                    ),
                    partner.name,
                    luxon.DateTime.fromISO(partner.cc_renewal_date).toLocaleString(
                        luxon.DateTime.DATE_FULL
                    )
                ),
                list: [
                    {
                        id: "renew",
                        label: component.env._t("Renew"),
                        isSelected: false,
                        item: "renew",
                    },
                    {
                        id: "stop",
                        label: component.env._t("Stop Coin"),
                        isSelected: false,
                        item: "stop",
                    },
                    {
                        id: "none",
                        label: component.env._t("Do nothing"),
                        isSelected: false,
                        item: "none",
                    },
                ],
                cancelText: component.env._t("Close"),
            });
            if (action === "stop") {
                await stopConnectionCoin(component, partner);
            } else if (action === "renew") {
                await addConnectionCoinRenewalProduct(component, partner);
            }
        }
        return true;
    }

    async function syncConnectionCoinDiscount(component, partner) {
        if (!getDiscountProductId(component)) {
            return;
        }
        if (!partner || !partner.cc_number) {
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
        partner.cc_forgotten = newCount;
        return newCount;
    }

    return {
        getDiscountProductId,
        applyDiscount,
        clearDiscount,
        stopConnectionCoin,
        isConnectionCoinValid,
        checkConnectionCoinExpiry,
        syncConnectionCoinDiscount,
        markConnectionCoinForgotten,
    };
});
