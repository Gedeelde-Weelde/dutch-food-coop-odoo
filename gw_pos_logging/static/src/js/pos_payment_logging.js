odoo.define("gw_pos_logging.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

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
            /**
             * Override to add logging when a new payment line is added
             */
            addNewPaymentLine({detail: paymentMethod}) {
                const result = super.addNewPaymentLine({detail: paymentMethod});

                if (result) {
                    const order = this.currentOrder;
                    const paymentLine =
                        order.get_paymentlines()[order.get_paymentlines().length - 1];

                    // Log the payment line addition
                    addLogToDb({
                        action: "add_payment",
                        payment_method: paymentMethod.name,
                        payment_method_id: paymentMethod.id,
                        amount: paymentLine.amount,
                        order_uid: order.uid,
                        order_name: order.name,
                        timestamp: new Date().toISOString(),
                    });
                }

                return result;
            }

            /**
             * Override to add logging when a payment line is deleted
             */
            deletePaymentLine(event) {
                const paymentLine = this.paymentLines.find(
                    (line) => line.cid === event.detail.cid
                );

                if (paymentLine) {
                    // Log the payment line deletion
                    addLogToDb({
                        action: "delete_payment",
                        payment_method: paymentLine.payment_method.name,
                        payment_method_id: paymentLine.payment_method.id,
                        amount: paymentLine.amount,
                        order_uid: this.currentOrder.uid,
                        order_name: this.currentOrder.name,
                        timestamp: new Date().toISOString(),
                    });
                }

                super.deletePaymentLine(event);
            }

            /**
             * Override to add logging when payment is validated
             */
            async _finalizeValidation() {
                // Log the payment validation
                const order = this.currentOrder;
                const paymentLines = order.get_paymentlines();

                for (const line of paymentLines) {
                    addLogToDb({
                        action: "validate_payment",
                        payment_method: line.payment_method.name,
                        payment_method_id: line.payment_method.id,
                        amount: line.amount,
                        order_uid: order.uid,
                        order_name: order.name,
                        timestamp: new Date().toISOString(),
                    });
                }

                return super._finalizeValidation();
            }
        };

    Registries.Component.extend(PaymentScreen, PosPaymentLoggingScreen);

    return PaymentScreen;
});
