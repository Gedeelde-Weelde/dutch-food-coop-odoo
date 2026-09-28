odoo.define(
    "gedeelde_weelde_custom.CustomerFacingDisplayReliability",
    function (require) {
        "use strict";

        const {PosGlobalState} = require("point_of_sale.models");
        const Registries = require("point_of_sale.Registries");

        const IMAGE_LOAD_TIMEOUT_MS = 5000;
        // Attribute set on the popup's <html> right after we paint it, so a
        // later health check can tell a live, styled popup apart from a
        // fresh/blank document (the browser discarded and reloaded a
        // backgrounded popup - win.closed stays false, but the document,
        // and everything we wrote into it, is gone).
        const PAINTED_ATTRIBUTE = "data-gw-customer-display-painted";

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
                        const timeoutId = setTimeout(
                            () => finish(null),
                            IMAGE_LOAD_TIMEOUT_MS
                        );
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

                // Paints the popup from scratch: head (every installed
                // module's CustomerFacingDisplayHead extension - stylesheets,
                // title, ...) and body, both freshly rendered from the same
                // live QWeb templates core uses. Used on the first click and
                // to repaint a popup the health check finds un-painted.
                // Keeping this as the one place that touches the popup's head
                // means there's a single source of truth for it (the real
                // template bundle) instead of a hand-maintained copy that can
                // drift out of sync with what modules actually add to it.
                async paint_customer_facing_display() {
                    const win = this.customer_display;
                    if (!win) return;
                    const rendered_html =
                        await this.render_html_for_customer_facing_display();
                    const $renderedHtml = $("<div>").html(rendered_html);
                    $(win.document.head).html($renderedHtml.find(".resources").html());
                    $(win.document.body).html(
                        $renderedHtml.find(".pos-customer_facing_display")
                    );
                    win.document.documentElement.setAttribute(PAINTED_ATTRIBUTE, "1");
                }

                is_customer_facing_display_painted() {
                    const win = this.customer_display;
                    if (!win) return false;
                    try {
                        return (
                            win.document.documentElement.getAttribute(
                                PAINTED_ATTRIBUTE
                            ) === "1"
                        );
                    } catch (error) {
                        return false;
                    }
                }

                send_current_order_to_customer_facing_display() {
                    if (!this.config.iface_customer_facing_display) return;
                    this.render_html_for_customer_facing_display().then(
                        (rendered_html) => {
                            if (this.customer_display) {
                                this._writeCustomerFacingDisplayBody(rendered_html);
                            } else if (
                                this.config.iface_customer_facing_display_via_proxy &&
                                this.env.proxy.posbox_supports_display
                            ) {
                                this.env.proxy.update_customer_facing_display(
                                    rendered_html
                                );
                            }
                        }
                    );
                }

                // Same body-only DOM write core always did on every order
                // change. The only change from core: the popup reference can
                // go stale (closed, or its document reset by the browser)
                // between one update and the next, and core let that throw
                // uncaught. Here a failed write just leaves the display stale
                // until the toolbar button's health check notices
                // (is_customer_facing_display_painted() above) and repaints
                // it, instead of crashing.
                _writeCustomerFacingDisplayBody(rendered_html) {
                    try {
                        const $renderedHtml = $("<div>").html(rendered_html);
                        $(this.customer_display.document.body).html(
                            $renderedHtml.find(".pos-customer_facing_display")
                        );
                        const orderlines = $(this.customer_display.document.body).find(
                            ".pos_orderlines_list"
                        );
                        orderlines.scrollTop(orderlines.prop("scrollHeight"));
                    } catch (error) {
                        // Window closed/reset - surfaced via the toolbar
                        // button's health check instead of failing here.
                    }
                }
            };

        Registries.Model.extend(PosGlobalState, CustomerFacingDisplayReliability);

        return PosGlobalState;
    }
);
