odoo.define("gw_connection_coin.CustomerFacingDisplayOrder", function (require) {
    "use strict";

    const {Order} = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");

    const GWConnectionCoinOrder = (Order) =>
        class extends Order {
            _getDiscountProductId() {
                return (
                    this.pos.config.discount_product_id &&
                    this.pos.config.discount_product_id[0]
                );
            }
            has_discount() {
                const discountProductId = this._getDiscountProductId();
                if (!discountProductId) {
                    return false;
                }
                return this.get_orderlines().some(
                    (line) => line.product.id === discountProductId
                );
            }
            // Sum of the discount lines added per tax group by the Discount
            // button (see gw_connection_coin.DiscountButton). These lines
            // carry a negative price, so this total is negative too.
            get_discount_total() {
                const discountProductId = this._getDiscountProductId();
                if (!discountProductId) {
                    return 0;
                }
                return this.get_orderlines()
                    .filter((line) => line.product.id === discountProductId)
                    .reduce((sum, line) => sum + line.get_price_with_tax(), 0);
            }
            // The order total before the connection-coin discount lines
            // were subtracted, i.e. what the customer would have paid
            // without the discount.
            get_total_before_discount() {
                return this.get_total_with_tax() - this.get_discount_total();
            }
        };

    Registries.Model.extend(Order, GWConnectionCoinOrder);

    return GWConnectionCoinOrder;
});
