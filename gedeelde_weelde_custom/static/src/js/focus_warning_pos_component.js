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

                this._mouseInside = true;
                this._windowFocused = document.hasFocus();

                this._updateWarning = () => {
                    const shouldWarn = !this._mouseInside && !this._windowFocused;
                    if (shouldWarn && !this.focusWarningState.show) {
                        this.focusWarningState.show = true;
                        this.playSound("bell");
                    } else if (!shouldWarn) {
                        this.focusWarningState.show = false;
                    }
                };

                this._onMouseLeave = () => {
                    this._mouseInside = false;
                    this._updateWarning();
                };

                this._onWindowBlur = () => {
                    this._windowFocused = false;
                    this._updateWarning();
                };

                this._onWindowFocus = () => {
                    this._windowFocused = true;
                    this._updateWarning();
                };

                onMounted(() => {
                    document.body.addEventListener("mouseleave", this._onMouseLeave);
                    document.body.addEventListener("mouseenter", this._onMouseEnter);
                    window.addEventListener("blur", this._onWindowBlur);
                    window.addEventListener("focus", this._onWindowFocus);
                });

                onWillUnmount(() => {
                    document.body.removeEventListener("mouseleave", this._onMouseLeave);
                    document.body.removeEventListener("mouseenter", this._onMouseEnter);
                    window.removeEventListener("blur", this._onWindowBlur);
                    window.removeEventListener("focus", this._onWindowFocus);
                });
            }
        };

    Registries.Component.extend(ProductScreen, FocusWarningProductScreen);

    return ProductScreen;
});
