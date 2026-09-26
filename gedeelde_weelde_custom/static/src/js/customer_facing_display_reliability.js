odoo.define("gedeelde_weelde_custom.CustomerFacingDisplayReliability", function (require) {
    "use strict";

    const { PosGlobalState } = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");

    const CUSTOMER_DISPLAY_STORAGE_KEY = "gw_customer_display_last_render";
    const IMAGE_LOAD_TIMEOUT_MS = 5000;

    const CustomerFacingDisplayReliability = (PosGlobalState) =>
        class extends PosGlobalState {
            // The original implementation only resolves the promise from
            // img.onload. If the image request errors out (a flaky network
            // request to /web/image, e.g.) onload never fires and this
            // promise hangs forever, which then hangs the Promise.all() in
            // render_html_for_customer_facing_display() for every order
            // containing that product until the POS session is reloaded -
            // freezing the customer display with no error anywhere. Add an
            // onerror fallback and a timeout so a broken image can never
            // block the display update.
            _convert_product_img_to_base64(product, url) {
                return new Promise((resolve) => {
                    const img = new Image();
                    let settled = false;
                    const finish = (dataURL) => {
                        if (settled) return;
                        settled = true;
                        resolve([product, dataURL]);
                    };
                    const timeoutId = setTimeout(() => finish(null), IMAGE_LOAD_TIMEOUT_MS);
                    img.onload = function () {
                        clearTimeout(timeoutId);
                        const canvas = document.createElement("CANVAS");
                        const ctx = canvas.getContext("2d");
                        canvas.height = this.height;
                        canvas.width = this.width;
                        ctx.drawImage(this, 0, 0);
                        finish(canvas.toDataURL("image/jpeg"));
                    };
                    img.onerror = function () {
                        clearTimeout(timeoutId);
                        finish(null);
                    };
                    img.crossOrigin = "use-credentials";
                    img.src = url;
                });
            }

            send_current_order_to_customer_facing_display() {
                if (!this.config.iface_customer_facing_display) return;
                this.render_html_for_customer_facing_display().then((rendered_html) => {
                    if (this.customer_display) {
                        this._publishCustomerDisplayRender(rendered_html);
                    } else if (
                        this.config.iface_customer_facing_display_via_proxy &&
                        this.env.proxy.posbox_supports_display
                    ) {
                        this.env.proxy.update_customer_facing_display(rendered_html);
                    }
                });
            }

            // Local mode used to reach directly into the popup's DOM
            // (`customer_display.document.body`). That is fragile: if the
            // browser discarded/reloaded the popup to save memory, or the
            // window was otherwise reset, the write either throws (silently,
            // since nothing here awaited/caught it) or lands in a document
            // that's about to be replaced - the display then sits frozen on
            // the last frame with no way to recover short of the cashier
            // noticing and re-clicking the button.
            //
            // Instead, publish the render to localStorage. The popup
            // (customer_facing_display.html) paints itself from this key on
            // load and on every native "storage" event, so it keeps working
            // even if it was reset while still open - no cross-window DOM
            // access required here at all, so this can never throw due to a
            // dead/stale window.
            _publishCustomerDisplayRender(rendered_html) {
                try {
                    const $renderedHtml = $("<div>").html(rendered_html);
                    const bodyHtml = $renderedHtml
                        .find(".pos-customer_facing_display")
                        .prop("outerHTML");
                    if (!bodyHtml) return;
                    window.localStorage.setItem(
                        CUSTOMER_DISPLAY_STORAGE_KEY,
                        JSON.stringify({ bodyHtml, savedAt: Date.now() })
                    );
                } catch (error) {
                    // localStorage can be unavailable (private browsing,
                    // quota exceeded) - the popup just won't update, nothing
                    // else we can do from here.
                }
            }
        };

    Registries.Model.extend(PosGlobalState, CustomerFacingDisplayReliability);

    return PosGlobalState;
});
