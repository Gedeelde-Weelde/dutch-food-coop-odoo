odoo.define("gw_connection_coin.DiscountButton", function (require) {
    "use strict";

    const DiscountButton = require("pos_discount.DiscountButton");

    // Monkey-patch pos_discount's apply_discount in place (rather than
    // subclassing via Registries.Component.extend) so that every caller
    // picks up the fix: both the on-screen Discount button and
    // gw_connection_coin.utils, which reuses this same prototype method
    // via DiscountButton.prototype.apply_discount.call(component, pc).
    //
    // This is a near-verbatim copy of core's apply_discount. The only
    // change is the sign check below: core only adds a discount line when
    // `discount < 0`, which silently drops the line whenever
    // baseToDiscount is negative (a return, where lines have a negative
    // quantity). That means a returned product never claws back the
    // connection-coin discount it was originally sold with. Widening the
    // check to `!== 0` lets a positive-priced line be added for that case
    // too. Diff against pos_discount/static/src/js/DiscountButton.js on
    // Odoo upgrades to keep this in sync.
    DiscountButton.prototype.apply_discount = async function (pc) {
        var order = this.env.pos.get_order();
        var lines = order.get_orderlines();
        var product = this.env.pos.db.get_product_by_id(
            this.env.pos.config.discount_product_id[0]
        );
        if (product === undefined) {
            await this.showPopup("ErrorPopup", {
                title: this.env._t("No discount product found"),
                body: this.env._t(
                    "The discount product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."
                ),
            });
            return;
        }

        // Remove existing discounts
        lines
            .filter((line) => line.get_product() === product)
            .forEach((line) => order.remove_orderline(line));

        // Add one discount line per tax group
        const linesByTax = order.get_orderlines_grouped_by_tax_ids();
        for (const [tax_ids, lines] of Object.entries(linesByTax)) {
            // Note that tax_ids_array is an Array of tax_ids that apply to these lines
            // That is, the use case of products with more than one tax is supported.
            const tax_ids_array = tax_ids
                .split(",")
                .filter((id) => id !== "")
                .map((id) => Number(id));

            const baseToDiscount = order.calculate_base_amount(
                tax_ids_array,
                lines.filter((ll) => ll.isGlobalDiscountApplicable())
            );

            // We add the price as manually set to avoid recomputation when changing customer.
            const discount = (-pc / 100.0) * baseToDiscount;
            if (discount !== 0) {
                order.add_product(product, {
                    price: discount,
                    lst_price: discount,
                    tax_ids: tax_ids_array,
                    merge: false,
                    description:
                        `${pc}%, ` +
                        (tax_ids_array.length
                            ? _.str.sprintf(
                                  this.env._t("Tax: %s"),
                                  tax_ids_array
                                      .map(
                                          (taxId) =>
                                              this.env.pos.taxes_by_id[taxId].amount +
                                              "%"
                                      )
                                      .join(", ")
                              )
                            : this.env._t("No tax")),
                    extras: {
                        price_automatically_set: true,
                    },
                });
            }
        }
    };

    return DiscountButton;
});
