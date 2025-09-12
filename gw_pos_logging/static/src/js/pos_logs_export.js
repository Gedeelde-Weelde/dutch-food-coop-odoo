odoo.define("gw_pos_logging.LogsExport", function (require) {
    "use strict";

    const DebugWidget = require("point_of_sale.DebugWidget");
    const Registries = require("point_of_sale.Registries");

    // Database name
    const paymentLogsDbName = "pos_payment_logs";

    // Add the export logs functionality to the DebugWidget
    const PosDebugWidgetWithExport = (DebugWidget) =>
        class extends DebugWidget {
            async exportLogs() {
                try {
                    // Show loading message
                    this.showNotification("Preparing logs for download...", 3000);

                    console.log("Export logs triggered from debug window");

                    // Get logs from payment logs database
                    const paymentLogs = await this.getLogsFromDb(
                        paymentLogsDbName,
                        "payment_logs"
                    );
                    console.log("Payment logs retrieved:", paymentLogs.length);

                    // Export payment logs as CSV
                    if (paymentLogs.length > 0) {
                        this.downloadLogsAsCSV(paymentLogs, "payment_logs");
                        this.showNotification("Logs exported successfully", 3000);
                    } else {
                        this.showNotification("No logs found to export", 3000);
                    }
                } catch (error) {
                    console.error("Error exporting logs:", error);
                    this.showNotification(
                        "Error exporting logs: " + error.message,
                        3000
                    );
                }
            }

            getLogsFromDb(dbName, storeName) {
                return new Promise((resolve, reject) => {
                    const request = indexedDB.open(dbName);

                    request.onerror = function (event) {
                        console.error(
                            `Error opening ${dbName}:`,
                            event.target.errorCode
                        );
                        reject(`Error opening ${dbName}`);
                    };

                    request.onsuccess = function (event) {
                        const db = event.target.result;
                        console.log(`Successfully opened database: ${dbName}`);
                        console.log(
                            `Object stores in database:`,
                            Array.from(db.objectStoreNames)
                        );

                        if (!db.objectStoreNames.contains(storeName)) {
                            console.warn(
                                `Store ${storeName} not found in database ${dbName}`
                            );
                            resolve([]);
                            return;
                        }

                        const transaction = db.transaction([storeName], "readonly");
                        const objectStore = transaction.objectStore(storeName);
                        const logs = [];

                        const cursorRequest = objectStore.openCursor();

                        cursorRequest.onsuccess = function (event) {
                            const cursor = event.target.result;
                            if (cursor) {
                                logs.push(cursor.value);
                                cursor.continue();
                            } else {
                                console.log(
                                    `Retrieved ${logs.length} logs from ${dbName}/${storeName}`
                                );
                                resolve(logs);
                            }
                        };

                        cursorRequest.onerror = function (event) {
                            console.error(
                                `Error retrieving logs from ${storeName}:`,
                                event.target.error
                            );
                            reject(`Error retrieving logs from ${storeName}`);
                        };
                    };
                });
            }

            downloadLogsAsCSV(logs, filename) {
                if (!logs || logs.length === 0) {
                    return;
                }

                // Get all unique keys from all log entries
                const allKeys = new Set();
                logs.forEach((log) => {
                    Object.keys(log).forEach((key) => allKeys.add(key));
                });

                // Convert Set to Array and sort for consistent column order
                const headers = Array.from(allKeys).sort();

                // Create CSV content
                let csvContent = headers.join(",") + "\n";

                logs.forEach((log) => {
                    const row = headers
                        .map((header) => {
                            const value = log[header];

                            // Handle different data types
                            if (value === null || value === undefined) {
                                return "";
                            } else if (typeof value === "object") {
                                // Convert objects to JSON strings
                                return (
                                    '"' +
                                    JSON.stringify(value).replace(/"/g, '""') +
                                    '"'
                                );
                            }
                            // Escape quotes and wrap in quotes if needed
                            const stringValue = String(value);
                            return stringValue.includes(",") ||
                                stringValue.includes('"') ||
                                stringValue.includes("\n")
                                ? '"' + stringValue.replace(/"/g, '""') + '"'
                                : stringValue;
                        })
                        .join(",");

                    csvContent += row + "\n";
                });

                // Create download link
                const blob = new Blob([csvContent], {type: "text/csv;charset=utf-8;"});
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");

                // Set filename with date for uniqueness
                const date = new Date().toISOString().slice(0, 10);
                link.setAttribute("href", url);
                link.setAttribute("download", `${filename}_${date}.csv`);
                link.style.visibility = "hidden";

                // Trigger download
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        };

    Registries.Component.extend(DebugWidget, PosDebugWidgetWithExport);

    return {
        PosDebugWidgetWithExport,
    };
});
