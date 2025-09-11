odoo.define("gw_pos_logging.OrderLogging", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const ReceiptScreen = require("point_of_sale.ReceiptScreen");
    const Registries = require("point_of_sale.Registries");
    const { Gui } = require("point_of_sale.Gui");

    // Database initialization
    const dbName = "pos_order_logs";
    const dbVersion = 2; // Increased version to trigger onupgradeneeded
    let db = null;

    // Initialize IndexedDB
    function initializeDatabase() {
        console.log("Initializing order logs database...");

        // First, check if the database exists
        const checkRequest = indexedDB.open(dbName);

        checkRequest.onerror = function(event) {
            console.error("Error checking database existence:", event.target.error);
        };

        checkRequest.onsuccess = function(event) {
            const existingDb = event.target.result;
            const currentVersion = existingDb.version;
            existingDb.close();

            console.log(`Database ${dbName} exists with version ${currentVersion}`);

            // Now open with proper version
            const request = indexedDB.open(dbName, dbVersion);

            request.onerror = function (event) {
                console.error("IndexedDB error:", event.target.error);
            };

            request.onupgradeneeded = function (event) {
                console.log(`Upgrading database from version ${event.oldVersion} to ${event.newVersion}`);
                db = event.target.result;

                // If the object store already exists, delete it to recreate
                if (db.objectStoreNames.contains("order_logs")) {
                    console.log("Deleting existing order_logs store");
                    db.deleteObjectStore("order_logs");
                }

                // Create the object store
                console.log("Creating order_logs store");
                const objectStore = db.createObjectStore("order_logs", {
                    keyPath: "id",
                    autoIncrement: true,
                });

                // Create indexes for searching as specified in the requirements
                objectStore.createIndex("timestamp", "timestamp", { unique: false });
                objectStore.createIndex("order_uid", "order_uid", { unique: false });
                objectStore.createIndex("action", "action", { unique: false });
                objectStore.createIndex("screen", "screen", { unique: false });

                console.log("Database schema updated successfully");
            };

            request.onsuccess = function (event) {
                db = event.target.result;
                console.log("Order Logs IndexedDB initialized successfully");
                console.log("Available object stores:", Array.from(db.objectStoreNames));

                // Add a test log entry to verify database is working
                addOrderLogToDb({
                    action: "database_init",
                    screen: "Initialization",
                    timestamp: new Date().toISOString(),
                    message: "Database initialization test entry"
                });
            };
        };
    }

    // Call the initialization function
    initializeDatabase();

    // Helper function to add a log entry to IndexedDB
    function addOrderLogToDb(logData) {
        if (!db) {
            console.error("Order logs database not initialized");
            return;
        }

        console.log("Adding order log to database:", logData);

        try {
            const transaction = db.transaction(["order_logs"], "readwrite");
            const objectStore = transaction.objectStore("order_logs");

            // Add timestamp if not provided
            if (!logData.timestamp) {
                logData.timestamp = new Date().toISOString();
            }

            const request = objectStore.add(logData);

            request.onsuccess = function (event) {
                console.log("Order log added successfully with ID:", event.target.result);
            };

            request.onerror = function (event) {
                console.error("Error adding order log:", event.target.error);
            };

            // Add transaction complete handler
            transaction.oncomplete = function() {
                console.log("Transaction completed successfully");
            };

            transaction.onerror = function(event) {
                console.error("Transaction error:", event.target.error);
            };
        } catch (error) {
            console.error("Exception while adding order log:", error);
        }
    }

    // Extend the ProductScreen to add logging functionality
    const PosProductLoggingScreen = (ProductScreen) =>
        class extends ProductScreen {
            /**
             * Override to add logging when a new order is created
             */
            _newOrderCreated() {
                const result = super._newOrderCreated();
                const order = this.env.pos.get_order();

                // Log the new order creation
                addOrderLogToDb({
                    action: "new_order",
                    screen: "ProductScreen",
                    order_uid: order.uid,
                    order_name: order.name,
                    timestamp: new Date().toISOString(),
                });

                return result;
            }

            /**
             * Override to add logging when a product is added to the order
             */
            async _clickProduct(event) {
                const result = await super._clickProduct(event);
                const order = this.env.pos.get_order();
                const product = event.detail;

                if (order && product) {
                    // Log the product addition
                    addOrderLogToDb({
                        action: "add_product",
                        screen: "ProductScreen",
                        order_uid: order.uid,
                        order_name: order.name,
                        product_id: product.id,
                        product_name: product.display_name,
                        timestamp: new Date().toISOString(),
                    });
                }

                return result;
            }

            /**
             * Override to add logging when a product is removed from the order
             */
            _removeOrderline(event) {
                const orderline = event.detail.orderline;
                const order = this.env.pos.get_order();

                if (order && orderline) {
                    // Log the product removal
                    addOrderLogToDb({
                        action: "remove_product",
                        screen: "ProductScreen",
                        order_uid: order.uid,
                        order_name: order.name,
                        product_id: orderline.product.id,
                        product_name: orderline.product.display_name,
                        quantity: orderline.get_quantity(),
                        timestamp: new Date().toISOString(),
                    });
                }

                super._removeOrderline(event);
            }

            /**
             * Override to add logging when quantity is changed
             */
            _updateSelectedOrderline(event) {
                const result = super._updateSelectedOrderline(event);
                const order = this.env.pos.get_order();
                const orderline = order.get_selected_orderline();

                if (order && orderline) {
                    // Log the quantity change
                    addOrderLogToDb({
                        action: "update_quantity",
                        screen: "ProductScreen",
                        order_uid: order.uid,
                        order_name: order.name,
                        product_id: orderline.product.id,
                        product_name: orderline.product.display_name,
                        quantity: orderline.get_quantity(),
                        timestamp: new Date().toISOString(),
                    });
                }

                return result;
            }

            /**
             * Override to add logging when an order is discarded
             */
            async _onClickDelete() {
                const order = this.env.pos.get_order();

                if (order) {
                    // Log the order discard
                    addOrderLogToDb({
                        action: "discard_order",
                        screen: "ProductScreen",
                        order_uid: order.uid,
                        order_name: order.name,
                        timestamp: new Date().toISOString(),
                    });
                }

                await super._onClickDelete();
            }

            /**
             * Override to add logging when transitioning to payment screen
             */
            async _onClickPay() {
                const order = this.env.pos.get_order();

                if (order) {
                    // Log the transition to payment screen
                    addOrderLogToDb({
                        action: "order_to_payment",
                        screen: "ProductScreen",
                        order_uid: order.uid,
                        order_name: order.name,
                        total_amount: order.get_total_with_tax(),
                        timestamp: new Date().toISOString(),
                    });
                }

                await super._onClickPay();
            }
        };

    // Extend the ReceiptScreen to add logging functionality
    const PosReceiptLoggingScreen = (ReceiptScreen) =>
        class extends ReceiptScreen {
            /**
             * Override to add logging when receipt screen is shown (order completed)
             */
            async willStart() {
                const result = await super.willStart();
                const order = this.env.pos.get_order();

                if (order) {
                    // Log the order completion
                    addOrderLogToDb({
                        action: "order_completed",
                        screen: "ReceiptScreen",
                        order_uid: order.uid,
                        order_name: order.name,
                        total_amount: order.get_total_with_tax(),
                        payment_methods: order.get_paymentlines().map(line => ({
                            name: line.payment_method.name,
                            amount: line.amount
                        })),
                        timestamp: new Date().toISOString(),
                    });
                }

                return result;
            }

            /**
             * Override to add logging when receipt is printed
             */
            async printReceipt() {
                const order = this.env.pos.get_order();

                if (order) {
                    // Log the receipt printing
                    addOrderLogToDb({
                        action: "print_receipt",
                        screen: "ReceiptScreen",
                        order_uid: order.uid,
                        order_name: order.name,
                        timestamp: new Date().toISOString(),
                    });
                }

                await super.printReceipt();
            }

            /**
             * Override to add logging when "Next Order" button is clicked
             */
            async nextScreen() {
                const order = this.env.pos.get_order();

                if (order) {
                    // Log the next order action
                    addOrderLogToDb({
                        action: "next_order",
                        screen: "ReceiptScreen",
                        order_uid: order.uid,
                        order_name: order.name,
                        timestamp: new Date().toISOString(),
                    });
                }

                await super.nextScreen();
            }
        };

    // Register error handling for POS operations
    const originalShowPopup = Gui.prototype.showPopup;
    Gui.prototype.showPopup = function (name, props) {
        // Log errors when error popups are shown
        if (name === 'ErrorPopup' || name === 'ErrorTracebackPopup') {
            const pos = this.env.pos;
            const order = pos ? pos.get_order() : null;

            addOrderLogToDb({
                action: "error",
                screen: this.env.screen ? this.env.screen.name : "unknown",
                error_type: name,
                error_message: props.body || props.message || "Unknown error",
                order_uid: order ? order.uid : null,
                order_name: order ? order.name : null,
                timestamp: new Date().toISOString(),
            });
        }

        return originalShowPopup.call(this, name, props);
    };

    // Register session events
    const originalStart = ProductScreen.prototype.mounted;
    ProductScreen.prototype.mounted = function () {
        if (originalStart) {
            originalStart.call(this);
        }

        // Log POS session start
        addOrderLogToDb({
            action: "session_start",
            screen: "ProductScreen",
            timestamp: new Date().toISOString(),
        });
    };

    Registries.Component.extend(ProductScreen, PosProductLoggingScreen);
    Registries.Component.extend(ReceiptScreen, PosReceiptLoggingScreen);

    return {
        ProductScreen,
        ReceiptScreen,
    };
});
