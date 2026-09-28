odoo.define(
    "gedeelde_weelde_custom.CustomerFacingDisplayButtonReliability",
    function (require) {
        "use strict";

        const CustomerFacingDisplayButton = require("point_of_sale.CustomerFacingDisplayButton");
        const Registries = require("point_of_sale.Registries");

        const LOCAL_POLL_INTERVAL_MS = 3000;

        const CustomerFacingDisplayButtonReliability = (CustomerFacingDisplayButton) =>
            class extends CustomerFacingDisplayButton {
                async onClickLocal() {
                    const customerDisplayWindow = window.open(
                        "",
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
                    await this.env.pos.paint_customer_facing_display();
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
                // so a display that died later kept showing "success" forever.
                // Mirror the proxy loop's cadence, and also self-heal a popup
                // the browser reset while backgrounded (blank but not
                // win.closed - see PosGlobalState.is_customer_facing_display_painted())
                // instead of just reporting it broken and waiting for the
                // cashier to notice and re-click.
                _startLocalHealthCheck() {
                    const self = this;
                    async function loop() {
                        const win = self.env.pos.customer_display;
                        if (!win || win.closed) {
                            self.state.status = "failure";
                        } else if (self.env.pos.is_customer_facing_display_painted()) {
                            self.state.status = "success";
                        } else {
                            try {
                                await self.env.pos.paint_customer_facing_display();
                                self.state.status = "success";
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
