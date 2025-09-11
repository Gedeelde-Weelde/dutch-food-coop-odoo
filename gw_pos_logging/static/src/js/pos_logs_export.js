odoo.define("gw_pos_logging.LogsExport", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const { useListener } = require("@web/core/utils/hooks");

    // Database names
    const paymentLogsDbName = "pos_payment_logs";
    const orderLogsDbName = "pos_order_logs"; // Ensure this matches exactly with the name in pos_order_logging.js

    class LogsExportButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }

        async onClick() {
            try {
                // Show loading message
                this.showTempMessage('Preparing logs for download...');

                console.log("Export button clicked - retrieving logs");

                // Force database deletion and recreation for order logs
                await this.resetOrderLogsDatabase();

                // Get logs from both databases
                const paymentLogs = await this.getLogsFromDb(paymentLogsDbName, "payment_logs");
                console.log("Payment logs retrieved:", paymentLogs.length);

                const orderLogs = await this.getLogsFromDb(orderLogsDbName, "order_logs");
                console.log("Order logs retrieved:", orderLogs.length);

                // Add a test entry to order logs if none exist
                if (orderLogs.length === 0) {
                    console.log("No order logs found, adding test entry");
                    await this.addTestOrderLog();
                    // Retrieve logs again
                    const updatedOrderLogs = await this.getLogsFromDb(orderLogsDbName, "order_logs");
                    console.log("Updated order logs count:", updatedOrderLogs.length);

                    if (updatedOrderLogs.length > 0) {
                        this.downloadLogsAsCSV(updatedOrderLogs, 'order_logs');
                    }
                } else {
                    // Export order logs as CSV
                    this.downloadLogsAsCSV(orderLogs, 'order_logs');
                }

                // Export payment logs as CSV
                if (paymentLogs.length > 0) {
                    this.downloadLogsAsCSV(paymentLogs, 'payment_logs');
                }

                if (paymentLogs.length === 0 && orderLogs.length === 0) {
                    this.showTempMessage('No logs found to export');
                } else {
                    this.showTempMessage('Logs exported successfully');
                }
            } catch (error) {
                console.error('Error exporting logs:', error);
                this.showTempMessage('Error exporting logs: ' + error.message);
            }
        }

        /**
         * Reset the order logs database to fix potential issues
         */
        async resetOrderLogsDatabase() {
            return new Promise((resolve, reject) => {
                console.log("Attempting to reset order logs database");

                // First try to delete the database
                const deleteRequest = indexedDB.deleteDatabase(orderLogsDbName);

                deleteRequest.onerror = function(event) {
                    console.error("Error deleting database:", event.target.error);
                    // Continue anyway
                    resolve();
                };

                deleteRequest.onsuccess = function() {
                    console.log("Database deleted successfully or didn't exist");

                    // Create a new database
                    const createRequest = indexedDB.open(orderLogsDbName, 1);

                    createRequest.onerror = function(event) {
                        console.error("Error creating database:", event.target.error);
                        reject(event.target.error);
                    };

                    createRequest.onupgradeneeded = function(event) {
                        console.log("Creating new order_logs database");
                        const db = event.target.result;

                        // Create the object store
                        const objectStore = db.createObjectStore("order_logs", {
                            keyPath: "id",
                            autoIncrement: true,
                        });

                        // Create indexes
                        objectStore.createIndex("timestamp", "timestamp", { unique: false });
                        objectStore.createIndex("order_uid", "order_uid", { unique: false });
                        objectStore.createIndex("action", "action", { unique: false });
                        objectStore.createIndex("screen", "screen", { unique: false });
                    };

                    createRequest.onsuccess = function(event) {
                        console.log("New database created successfully");
                        resolve();
                    };
                };
            });
        }

        /**
         * Add a test log entry to the order logs database
         */
        async addTestOrderLog() {
            return new Promise((resolve, reject) => {
                const request = indexedDB.open(orderLogsDbName);

                request.onerror = function(event) {
                    console.error("Error opening database:", event.target.error);
                    reject(event.target.error);
                };

                request.onsuccess = function(event) {
                    const db = event.target.result;

                    try {
                        const transaction = db.transaction(["order_logs"], "readwrite");
                        const objectStore = transaction.objectStore("order_logs");

                        const testLog = {
                            action: "test_entry",
                            screen: "LogsExport",
                            timestamp: new Date().toISOString(),
                            message: "This is a test entry to verify order logs export functionality"
                        };

                        const addRequest = objectStore.add(testLog);

                        addRequest.onsuccess = function(event) {
                            console.log("Test log added successfully");
                            resolve();
                        };

                        addRequest.onerror = function(event) {
                            console.error("Error adding test log:", event.target.error);
                            reject(event.target.error);
                        };
                    } catch (error) {
                        console.error("Exception adding test log:", error);
                        reject(error);
                    }
                };
            });
        }

        /**
         * Retrieve all logs from the specified database and object store
         */
        getLogsFromDb(dbName, storeName) {
            console.log(`Attempting to get logs from database: ${dbName}, store: ${storeName}`);
            return new Promise((resolve, reject) => {
                const request = indexedDB.open(dbName);

                request.onerror = function(event) {
                    console.error(`Error opening ${dbName}:`, event.target.errorCode);
                    reject(`Error opening ${dbName}`);
                };

                request.onsuccess = function(event) {
                    const db = event.target.result;
                    console.log(`Successfully opened database: ${dbName}`);
                    console.log(`Object stores in database:`, Array.from(db.objectStoreNames));

                    if (!db.objectStoreNames.contains(storeName)) {
                        console.warn(`Store ${storeName} not found in database ${dbName}`);
                        resolve([]);
                        return;
                    }

                    const transaction = db.transaction([storeName], "readonly");
                    const objectStore = transaction.objectStore(storeName);
                    const logs = [];

                    const cursorRequest = objectStore.openCursor();

                    cursorRequest.onsuccess = function(event) {
                        const cursor = event.target.result;
                        if (cursor) {
                            logs.push(cursor.value);
                            cursor.continue();
                        } else {
                            console.log(`Retrieved ${logs.length} logs from ${dbName}/${storeName}`);
                            resolve(logs);
                        }
                    };

                    cursorRequest.onerror = function(event) {
                        console.error(`Error retrieving logs from ${storeName}:`, event.target.error);
                        reject(`Error retrieving logs from ${storeName}`);
                    };
                };
            });
        }

        /**
         * Convert logs to CSV format and trigger download
         */
        downloadLogsAsCSV(logs, filename) {
            if (!logs || logs.length === 0) {
                return;
            }

            // Get all unique keys from all log entries
            const allKeys = new Set();
            logs.forEach(log => {
                Object.keys(log).forEach(key => allKeys.add(key));
            });

            // Convert Set to Array and sort for consistent column order
            const headers = Array.from(allKeys).sort();

            // Create CSV content
            let csvContent = headers.join(',') + '\n';

            logs.forEach(log => {
                const row = headers.map(header => {
                    const value = log[header];

                    // Handle different data types
                    if (value === null || value === undefined) {
                        return '';
                    } else if (typeof value === 'object') {
                        // Convert objects to JSON strings
                        return '"' + JSON.stringify(value).replace(/"/g, '""') + '"';
                    } else {
                        // Escape quotes and wrap in quotes if needed
                        const stringValue = String(value);
                        return stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')
                            ? '"' + stringValue.replace(/"/g, '""') + '"'
                            : stringValue;
                    }
                }).join(',');

                csvContent += row + '\n';
            });

            // Create download link
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');

            // Set filename with date for uniqueness
            const date = new Date().toISOString().slice(0, 10);
            link.setAttribute('href', url);
            link.setAttribute('download', `${filename}_${date}.csv`);
            link.style.visibility = 'hidden';

            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        /**
         * Show a temporary message to the user
         */
        showTempMessage(message) {
            this.showNotification(message, 3000);
        }
    }

    LogsExportButton.template = 'LogsExportButton';

    // Register the component
    Registries.Component.add(LogsExportButton);

    // Add the button to the ProductScreen
    const PosProductScreenWithExport = (ProductScreen) =>
        class extends ProductScreen {
            setup() {
                super.setup();
            }
        };

    Registries.Component.extend(ProductScreen, PosProductScreenWithExport);

    return {
        LogsExportButton,
        PosProductScreenWithExport,
    };
});
