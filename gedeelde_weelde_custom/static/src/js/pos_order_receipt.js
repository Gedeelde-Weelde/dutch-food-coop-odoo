odoo.define("gedeelde_weelde_custom.Order", function (require) {
    "use strict";

    var utils = require('web.utils');
    var round_pr = utils.round_precision;

    const { Order } = require('point_of_sale.models');
    const Registries = require("point_of_sale.Registries");

    const CustomOrder = (Order) =>
        class extends Order {
            get_total_without_discount_lines() {
                const normalOrderLines = this.orderlines.filter(orderline => orderline.product.default_code !== 'DISC')
                return round_pr(normalOrderLines.reduce((function (sum, orderLine) {
                    return sum + orderLine.get_price_with_tax();
                }), 0), this.pos.currency.rounding);
            }
            get_total_of_discount_lines() {
                const discountOrderLines = this.orderlines.filter(orderline => orderline.product.default_code === 'DISC')
                return round_pr(discountOrderLines.reduce((function (sum, orderLine) {
                    return sum + orderLine.get_price_with_tax();
                }), 0), this.pos.currency.rounding);
            }
            export_for_printing() {
                let receipt = super.export_for_printing();
                receipt.total_without_discount_lines = this.get_total_without_discount_lines();
                receipt.total_of_discount_lines = this.get_total_of_discount_lines();
                return receipt;
            }
        };

    Registries.Model.extend(Order, CustomOrder);

    return CustomOrder;
});
