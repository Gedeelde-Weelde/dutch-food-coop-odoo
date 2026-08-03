odoo.define("gw_connection_coin.CustomerFacingDisplayOrder", function (require) {
    "use strict";

    const { Order } = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");

    const GWConnectionCoinOrder = (Order) =>
        class extends Order {
            has_discount() {
                const discountProductId =
                    this.pos.config.discount_product_id &&
                    this.pos.config.discount_product_id[0];
                if (!discountProductId) {
                    return false;
                }
                return this.get_orderlines().some(
                    (line) => line.product.id === discountProductId
                );
            }
        };

    Registries.Model.extend(Order, GWConnectionCoinOrder);

    return GWConnectionCoinOrder;
});
