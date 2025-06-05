odoo.define('gedeelde_weelde_custom.BarcodeParser', function (require) {
    "use strict";

    const BarcodeParser = require('barcodes.BarcodeParser');
    const Chrome = require('point_of_sale.Chrome');

// Extend the BarcodeParser to include price_check_digit field and rule information
    const CustomBarcodeParser = BarcodeParser.extend({
        _barcodeRuleFields: function () {
            const fields = this._super();
            fields.push('price_check_digit');
            return fields;
        },

        parse_barcode: function(barcode) {
            console.debug('Custom barcode parser called with barcode:', barcode);
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
                        console.debug('Rule matched:', rule);
                        break;
                    }
                }
            }

            return parsed_result;
        }
    });

// Override Chrome's setupBarcodeParser to use our custom parser
    const Registries = require('point_of_sale.Registries');

    const CustomChrome = Chrome =>
        class extends Chrome {
            setupBarcodeParser() {
                if (!this.env.pos.company.nomenclature_id) {
                    const errorMessage = this.env._t("The barcode nomenclature setting is not configured. " +
                        "Make sure to configure it on your Point of Sale configuration settings");
                    throw new Error(this.env._t("Missing barcode nomenclature"), { cause: { message: errorMessage } });
                }

                console.debug('Setting up custom barcode parser');
                const barcode_parser = new CustomBarcodeParser({ nomenclature_id: this.env.pos.company.nomenclature_id });
                this.env.barcode_reader.set_barcode_parser(barcode_parser);

                const fallbackNomenclature = this.env.pos.company.fallback_nomenclature_id;
                if (fallbackNomenclature) {
                    const fallbackBarcodeParser = new CustomBarcodeParser({ nomenclature_id: fallbackNomenclature });
                    this.env.barcode_reader.setFallbackBarcodeParser(fallbackBarcodeParser);
                }

                return barcode_parser.is_loaded();
            }
        };

    Registries.Component.extend(Chrome, CustomChrome);

    return CustomBarcodeParser;
});
