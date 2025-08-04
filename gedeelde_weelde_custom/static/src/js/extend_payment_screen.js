odoo.define("gedeelde_weelde_custom.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const CustomPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            addNewPaymentLine({detail: paymentMethod}) {
                const result = super.addNewPaymentLine({detail: paymentMethod});

                if (result) {
                    console.log("Adding new payment line", paymentMethod.cid);
                    this.enableInvoice(paymentMethod);
                }

                return result;
            }

            enableInvoice(paymentMethod) {
                if (paymentMethod.type === "pay_later") {
                    if (!this.currentOrder.is_to_invoice()) {
                        this.toggleIsToInvoice();
                    }
                }
            }

            disableInvoice(paymentMethod) {
                if (paymentMethod.type === "pay_later") {
                    if (this.currentOrder.is_to_invoice()) {
                        this.toggleIsToInvoice();
                    }
                }
            }

            deletePaymentLine(event) {
                const line = this.paymentLines.find(
                    (line) => line.cid === event.detail.cid
                );
                const paymentMethod = line.payment_method;
                if (paymentMethod) {
                    this.disableInvoice(paymentMethod);
                }

                super.deletePaymentLine(event);
            }
        };

    Registries.Component.extend(PaymentScreen, CustomPaymentScreen);

    return PaymentScreen;
});
