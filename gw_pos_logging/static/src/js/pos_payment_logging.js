odoo.define("gw_pos_logging.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");
    const {isConnectionError} = require("point_of_sale.utils");
    const utils = require("web.utils");

    // Database initialization
    const dbName = "pos_payment_logs";
    const dbVersion = 1;
    let db = null;

    // Initialize IndexedDB
    const request = indexedDB.open(dbName, dbVersion);

    request.onerror = function (event) {
        console.error("IndexedDB error:", event.target.errorCode);
    };

    request.onupgradeneeded = function (event) {
        db = event.target.result;

        // Create an object store for payment logs if it doesn't exist
        if (!db.objectStoreNames.contains("payment_logs")) {
            const objectStore = db.createObjectStore("payment_logs", {
                keyPath: "id",
                autoIncrement: true,
            });

            // Create indexes for searching
            objectStore.createIndex("timestamp", "timestamp", {unique: false});
            objectStore.createIndex("payment_method", "payment_method", {
                unique: false,
            });
            objectStore.createIndex("amount", "amount", {unique: false});
        }
    };

    request.onsuccess = function (event) {
        db = event.target.result;
        console.log("IndexedDB initialized successfully");
    };

    // Helper function to add a log entry to IndexedDB
    function addLogToDb(logData) {
        if (!db) {
            console.error("Database not initialized");
            return;
        }

        const transaction = db.transaction(["payment_logs"], "readwrite");
        const objectStore = transaction.objectStore("payment_logs");

        // Add timestamp if not provided
        if (!logData.timestamp) {
            logData.timestamp = new Date().toISOString();
        }

        const request = objectStore.add(logData);

        request.onsuccess = function () {
            console.log("Payment log added successfully");
        };

        request.onerror = function (event) {
            console.error("Error adding payment log:", event.target.error);
        };
    }

    // Extend the PaymentScreen to add logging functionality
    const PosPaymentLoggingScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async _sendPaymentRequest({detail: line}) {
                const order = this.currentOrder;
                // Other payment lines can not be reversed anymore
                const methods = [];
                for (const line of this.paymentLines) {
                    methods.push(line.payment_method.name);
                }

                addLogToDb({
                    action: "_send_payment_request",
                    order_name: order.name,
                    payment_method: methods.join(", "),
                    total_amount: order.get_total_with_tax(),
                    timestamp: new Date().toISOString(),
                });
                this.paymentLines.forEach(function (line) {
                    line.can_be_reversed = false;
                });

                const payment_terminal = line.payment_method.payment_terminal;
                line.set_payment_status("waiting");

                const isPaymentSuccessful = await payment_terminal.send_payment_request(
                    line.cid
                );
                if (isPaymentSuccessful) {
                    addLogToDb({
                        action: "_send_payment_request_successful",
                        order_name: order.name,
                        payment_method: methods.join(", "),
                        total_amount: order.get_total_with_tax(),
                        timestamp: new Date().toISOString(),
                    });

                    line.set_payment_status("done");
                    line.can_be_reversed = payment_terminal.supports_reversals;
                    // Automatically validate the order when after an electronic payment,
                    // the current order is fully paid and due is zero.
                    if (
                        this.currentOrder.is_paid() &&
                        utils.float_is_zero(
                            this.currentOrder.get_due(),
                            this.env.pos.currency.decimal_places
                        )
                    ) {
                        this.trigger("validate-order");
                    }
                } else {
                    addLogToDb({
                        action: "_send_payment_request_unsuccessful",
                        order_name: order.name,
                        payment_method: methods.join(", "),
                        total_amount: order.get_total_with_tax(),
                        timestamp: new Date().toISOString(),
                    });

                    line.set_payment_status("retry");
                }
            }

            async validateOrder(isForceValidate) {
                const order = this.currentOrder;
                const methods = [];
                for (const line of this.paymentLines) {
                    methods.push(line.payment_method.name);
                }
                addLogToDb({
                    action: "validate_order",
                    order_name: order.name,
                    payment_method: methods.join(", "),
                    total_amount: order.get_total_with_tax(),
                    timestamp: new Date().toISOString(),
                });

                await super.validateOrder(isForceValidate);
            }
            async _isOrderValid(isForceValidate) {
                const order = this.currentOrder;
                addLogToDb({
                    action: "_is_order_valid",
                    order_name: order.name,
                    total_amount: order.get_total_with_tax(),
                    timestamp: new Date().toISOString(),
                });

                return await super._isOrderValid(isForceValidate);
            }
            /**
             * Override to ad d logging when payment is validated
             */
            async _finalizeValidation() {
                const order = this.currentOrder;
                addLogToDb({
                    action: "start_finialize_validation",
                    order_name: order.name,
                    total_amount: order.get_total_with_tax(),
                    timestamp: new Date().toISOString(),
                });

                if (
                    (this.currentOrder.is_paid_with_cash() ||
                        this.currentOrder.get_change()) &&
                    this.env.pos.config.iface_cashdrawer &&
                    this.env.proxy &&
                    this.env.proxy.printer
                ) {
                    this.env.proxy.printer.open_cashbox();
                }

                this.currentOrder.initialize_validation_date();
                for (const line of this.paymentLines) {
                    if (!line.amount === 0) {
                        this.currentOrder.remove_paymentline(line);
                    }
                    addLogToDb({
                        action: "looping_over_payment_lines",
                        payment_method: line.payment_method.name,
                        payment_method_id: line.payment_method.id,
                        order_name: order.name,
                        total_amount: order.get_total_with_tax(),
                        timestamp: new Date().toISOString(),
                    });
                }
                this.currentOrder.finalized = true;

                // eslint-disable-next-line init-declarations
                let syncOrderResult, hasError;

                try {
                    this.env.services.ui.block();
                    addLogToDb({
                        action: "start_syncing_order",
                        order_name: order.name,
                        total_amount: order.get_total_with_tax(),
                        timestamp: new Date().toISOString(),
                    });

                    // 1. Save order to server.
                    syncOrderResult = await this.env.pos.push_single_order(
                        this.currentOrder
                    );

                    addLogToDb({
                        action: "end_syncing_order",
                        order_pos_reference: order.order_pos_reference,
                        order_name: order.name,
                        total_amount: order.get_total_with_tax(),
                        timestamp: new Date().toISOString(),
                    });

                    // 2. Invoice.
                    if (
                        this.shouldDownloadInvoice() &&
                        this.currentOrder.is_to_invoice()
                    ) {
                        if (syncOrderResult.length) {
                            await this.doInvoice(syncOrderResult[0].account_move);
                        } else {
                            throw {
                                code: 401,
                                message: "Backend Invoice",
                                data: {order: this.currentOrder},
                            };
                        }
                    }

                    // 3. Post process.
                    if (
                        syncOrderResult.length &&
                        this.currentOrder.wait_for_push_order()
                    ) {
                        const postPushResult = await this._postPushOrderResolve(
                            this.currentOrder,
                            syncOrderResult.map((res) => res.id)
                        );
                        if (!postPushResult) {
                            addLogToDb({
                                action: "order_not_pushed",
                                order_name: order.name,
                                total_amount: order.get_total_with_tax(),
                                timestamp: new Date().toISOString(),
                            });
                            this.showPopup("ErrorPopup", {
                                title: this.env._t("Error: no internet connection."),
                                body: this.env._t(
                                    "Some, if not all, post-processing after syncing order failed."
                                ),
                            });
                        }
                    }
                } catch (error) {
                    // Unblock the UI before showing the error popup
                    this.env.services.ui.unblock();
                    if (error.code == 700 || error.code == 701) this.error = true;

                    if ("code" in error) {
                        // We started putting `code` in the rejected object for invoicing error.
                        // We can continue with that convention such that when the error has `code`,
                        // then it is an error when invoicing. Besides, _handlePushOrderError was
                        // introduce to handle invoicing error logic.
                        await this._handlePushOrderError(error);
                    } else {
                        // We don't block for connection error. But we rethrow for any other errors.
                        // eslint-disable-next-line no-lonely-if
                        if (isConnectionError(error)) {
                            this.showPopup("OfflineErrorPopup", {
                                title: this.env._t("Connection Error"),
                                body: this.env._t(
                                    "Order is not synced. Check your internet connection"
                                ),
                            });
                        } else {
                            throw error;
                        }
                    }
                } finally {
                    this.env.services.ui.unblock();
                    // Always show the next screen regardless of error since pos has to
                    // continue working even offline.
                    this.showScreen(this.nextScreen);
                    // Remove the order from the local storage so that when we refresh the page, the order
                    // won't be there
                    this.env.pos.db.remove_unpaid_order(this.currentOrder);
                    addLogToDb({
                        action: "final_validation",
                        order_name: order.name,
                        total_amount: order.get_total_with_tax(),
                        remaining_orders: this.env.pos.db.get_orders().length,
                        timestamp: new Date().toISOString(),
                    });

                    // Ask the user to sync the remaining unsynced orders.
                    if (
                        !hasError &&
                        syncOrderResult &&
                        this.env.pos.db.get_orders().length
                    ) {
                        const {confirmed} = await this.showPopup("ConfirmPopup", {
                            title: this.env._t("Remaining unsynced orders"),
                            body: this.env._t(
                                "There are unsynced orders. Do you want to sync these orders?"
                            ),
                        });
                        if (confirmed) {
                            // NOTE: Not yet sure if this should be awaited or not.
                            // If awaited, some operations like changing screen
                            // might not work.
                            this.env.pos.push_orders();
                        }
                    }
                }
            }
        };

    Registries.Component.extend(PaymentScreen, PosPaymentLoggingScreen);

    return PaymentScreen;
});
