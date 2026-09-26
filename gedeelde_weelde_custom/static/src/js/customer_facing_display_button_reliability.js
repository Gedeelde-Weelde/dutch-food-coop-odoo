odoo.define(
    "gedeelde_weelde_custom.CustomerFacingDisplayButtonReliability",
    function (require) {
        "use strict";

        const CustomerFacingDisplayButton = require("point_of_sale.CustomerFacingDisplayButton");
        const Registries = require("point_of_sale.Registries");

        const LOCAL_POLL_INTERVAL_MS = 3000;
        const CUSTOMER_DISPLAY_URL =
            "/gedeelde_weelde_custom/static/src/html/customer_facing_display.html";

        const CustomerFacingDisplayButtonReliability = (CustomerFacingDisplayButton) =>
            class extends CustomerFacingDisplayButton {
                async onClickLocal() {
                    const customerDisplayWindow = window.open(
                        CUSTOMER_DISPLAY_URL,
                        "Customer Display",
                        "height=600,width=900"
                    );
                    if (!customerDisplayWindow) {
                        // Popup blocked by the browser - previously this threw
                        // (window.open returned null, then code tried to read
                        // null.document) with no visible feedback at all.
                        this.state.status = "failure";
                        return;
                    }
                    this.env.pos.customer_display = customerDisplayWindow;
                    // Seed it immediately so it doesn't sit on "Waiting for the
                    // till" until the next order change.
                    this.env.pos.send_current_order_to_customer_facing_display();
                    this.state.status = "success";
                }

                _start() {
                    if (!this.local) {
                        return super._start();
                    }
                    this._startLocalHealthCheck();
                }

                // Unlike proxy mode, local mode never polled anything: the
                // toolbar status was set once on click and then never revisited,
                // so a display that died later kept showing "Disconnected: no"
                // (or rather, kept showing success) forever. Mirror the proxy
                // loop's cadence so the cashier gets an honest, live status.
                _startLocalHealthCheck() {
                    const self = this;
                    function loop() {
                        const win = self.env.pos.customer_display;
                        if (!win) {
                            self.state.status = "failure";
                        } else {
                            // Note: `env.pos.customer_display` is never reset to
                            // null/undefined here - the reactive setter for it
                            // runs the new value through owl's markRaw(), which
                            // throws on null/undefined ("WeakSet value ... must
                            // be an object"). Re-checking win.closed on every
                            // tick is enough to report the right status without
                            // ever needing to clear the reference; onClickLocal
                            // simply overwrites it with a fresh window later.
                            try {
                                self.state.status = win.closed ? "failure" : "success";
                            } catch (error) {
                                self.state.status = "failure";
                            }
                        }
                        setTimeout(loop, LOCAL_POLL_INTERVAL_MS);
                    }
                    loop();
                }
            };

        Registries.Component.extend(
            CustomerFacingDisplayButton,
            CustomerFacingDisplayButtonReliability
        );

        return CustomerFacingDisplayButton;
    }
);
