odoo.define("sale_pricelist_discount_info.models", function (require) {
    "use strict";

    const models = require("point_of_sale.models");
    const Orderline = models.Orderline;

    /**
     * Extend Orderline to include pricelist discount information
     */
    models.Orderline = class OrderlineWithDiscount extends Orderline {
        constructor(obj, options) {
            super(...arguments);
            this.original_price = 0;
            this.discounted_price = 0;
        }

        init_from_JSON(json) {
            super.init_from_JSON(json);
            this.original_price = json.original_price || 0;
            this.discounted_price = json.discounted_price || 0;
        }

        export_as_JSON() {
            const json = super.export_as_JSON();
            json.original_price = this.original_price;
            json.discounted_price = this.discounted_price;
            return json;
        }

        set_unit_price(price) {
            super.set_unit_price(price);
            this._compute_discount_info();
        }

        set_quantity(quantity) {
            super.set_quantity(quantity);
            this._compute_discount_info();
        }

        /**
         * Compute the original price and discounted price based on pricelist
         */
        _compute_discount_info() {
            if (!this.product || !this.order || !this.order.pricelist) {
                this.original_price = this.price;
                this.discounted_price = this.price;
                return;
            }

            // Original price is the product's list price
            this.original_price = this.product.lst_price;

            // Discounted price depends on pricelist discount policy
            const pricelist = this.order.pricelist;

            if (pricelist.discount_policy === "without_discount") {
                // In this mode, price_unit is the list price and discount % is applied
                this.discounted_price = this.original_price * (1.0 - (this.discount || 0.0) / 100.0);
            } else {
                // "with_discount" (default): price_unit IS the discounted price
                this.discounted_price = this.price;
            }
        }
    };

    return models;
});
