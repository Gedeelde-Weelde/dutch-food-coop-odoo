odoo.define("gedeelde_weelde_custom.FocusWarning", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const {onMounted, onWillUnmount, useState} = owl;

    const FocusWarningProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            setup() {
                super.setup();

                this.focusWarningState = useState({show: false});

                this._onMouseLeave = () => {
                    this.focusWarningState.show = true;
                    this.playSound("error");
                };

                this._onMouseEnter = () => {
                    this.focusWarningState.show = false;
                };

                onMounted(() => {
                    document.body.addEventListener("mouseleave", this._onMouseLeave);
                    document.body.addEventListener("mouseenter", this._onMouseEnter);
                });

                onWillUnmount(() => {
                    document.body.removeEventListener("mouseleave", this._onMouseLeave);
                    document.body.removeEventListener("mouseenter", this._onMouseEnter);
                });
            }
        };

    Registries.Component.extend(ProductScreen, FocusWarningProductScreen);

    return ProductScreen;
});
