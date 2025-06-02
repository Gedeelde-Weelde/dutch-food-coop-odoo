odoo.define('product_import_cwa.orderline_override', function (require) {
    'use strict';

    const models = require('point_of_sale.models');

    // Store the original methods
    const _super_set_quantity = models.Orderline.prototype.set_quantity;
    const _super_set_unit_price = models.Orderline.prototype.set_unit_price;

    // Override set_quantity method
    models.Orderline.prototype.set_quantity = function(quantity, keep_price) {
        // Call the original method
        _super_set_quantity.call(this, quantity, keep_price);
        console.log('set_quantity called with:', quantity);
        console.log('this:', this);
        console.log('discount:', this.discount);

        // Trigger pricelist recalculation after quantity change for weighted products
        if (this.product.to_weight && this.quantity > 0) {
            try {
                // Use the order's get_applicable_pricelist instead of compute_all_prices
                const order = this.pos.get_order();
                console.log('Order:', order);
                if (order && order.pricelist) {
                    const price = this.product.get_price(order.pricelist, this.quantity);
                    if (price !== undefined) {
                        this.set_unit_price(price);
                    }
                }

                // Trigger order update to refresh UI
                if (order) {
                    order.trigger('change', order);
                }

                console.log('Weighted product price recalculated:', {
                    product: this.product.display_name,
                    quantity: this.quantity,
                    price: this.price,
                    discount: this.discount
                });
            } catch (error) {
                console.error('Error recalculating weighted product price:', error);
            }
        }
    };

    // Override set_unit_price method
    models.Orderline.prototype.set_unit_price = function(price) {
        // Call the original method
        _super_set_unit_price.call(this, price);
        console.log('set_unit_price called with:', price, this.discount);

        if (this.product.to_weight) {
            // Force order update to refresh UI for weighted products
            if (this.order) {
                // this.order.trigger('change', this.order);
            }
        }
    };

    return models;
});
