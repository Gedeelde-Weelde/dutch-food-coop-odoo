odoo.define('gedeelde_weelde_custom.PaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const CustomPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            addNewPaymentLine({ detail: paymentMethod }) {
                const result = super.addNewPaymentLine({ detail: paymentMethod });

                this.handleInvoiceToggle(result, paymentMethod);

                return result;
            }

            handleInvoiceToggle(result, paymentMethod) {
                if (result && paymentMethod.type === 'pay_later') {
                    if (!this.currentOrder.is_to_invoice()) {
                        this.toggleIsToInvoice();
                    }
                }
            }
        };

    Registries.Component.extend(PaymentScreen, CustomPaymentScreen);

    return PaymentScreen;
});
