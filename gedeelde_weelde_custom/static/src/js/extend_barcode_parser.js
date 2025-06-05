odoo.define('gedeelde_weelde_custom.BarcodeParser', function (require) {
    "use strict";
    console.debug('-------------- Barcode parser loaded');
    const BarcodeParser = require('barcodes.BarcodeParser');

    const CustomBarcodeParser = BarcodeParser.extend({
        _barcodeRuleFields: function () {
            const fields = this._super();
            fields.push('price_check_digit');
            return fields;
        },

        parse_barcode: function(barcode) {
            console.debug('Barcode parser called with barcode:', barcode);
            const parsed_result = this._super(barcode);

            // Add rule information to the parsed result
            if (parsed_result.type !== 'error' && this.nomenclature) {
                const rules = this.nomenclature.rules;
                for (let i = 0; i < rules.length; i++) {
                    const rule = rules[i];
                    let cur_barcode = barcode;

                    if (rule.encoding === 'ean13' &&
                        this.check_encoding(barcode,'upca') &&
                        this.nomenclature.upc_ean_conv in {'upc2ean':'','always':''}) {
                        cur_barcode = '0' + cur_barcode;
                    } else if (rule.encoding === 'upca' &&
                        this.check_encoding(barcode,'ean13') &&
                        barcode[0] === '0' &&
                        this.nomenclature.upc_ean_conv in {'ean2upc':'','always':''}) {
                        cur_barcode = cur_barcode.substr(1,12);
                    }

                    if (!this.check_encoding(cur_barcode, rule.encoding)) {
                        continue;
                    }

                    const match = this.match_pattern(cur_barcode, rule.pattern, rule.encoding);
                    if (match.match) {
                        parsed_result.rule = rule;
                        break;
                    }
                }
            }

            return parsed_result;
        }
    });

    return CustomBarcodeParser;
});
