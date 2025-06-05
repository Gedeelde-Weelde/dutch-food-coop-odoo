odoo.define("gedeelde_weelde_custom.BarcodeParserExtension", function (require) {
    "use strict";

    const BarcodeParser = require("barcodes.BarcodeParser");

    // Store the original methods
    const originalBarcodeRuleFields = BarcodeParser.prototype._barcodeRuleFields;
    const originalParseBarcode = BarcodeParser.prototype.parse_barcode;

    // Extend _barcodeRuleFields to include our custom field
    BarcodeParser.prototype._barcodeRuleFields = function () {
        const fields = originalBarcodeRuleFields.call(this);
        fields.push("price_check_digit");
        return fields;
    };

    BarcodeParser.prototype._addRuleInformationToParsedResult = function (
        parsed_result,
        barcode
    ) {
        if (parsed_result.type !== "error" && this.nomenclature) {
            const rules = this.nomenclature.rules;
            for (let i = 0; i < rules.length; i++) {
                const rule = rules[i];
                let cur_barcode = barcode;

                if (
                    rule.encoding === "ean13" &&
                    this.check_encoding(barcode, "upca") &&
                    this.nomenclature.upc_ean_conv in {upc2ean: "", always: ""}
                ) {
                    cur_barcode = "0" + cur_barcode;
                } else if (
                    rule.encoding === "upca" &&
                    this.check_encoding(barcode, "ean13") &&
                    barcode[0] === "0" &&
                    this.nomenclature.upc_ean_conv in {ean2upc: "", always: ""}
                ) {
                    cur_barcode = cur_barcode.substr(1, 12);
                }

                if (!this.check_encoding(cur_barcode, rule.encoding)) {
                    continue;
                }

                const match = this.match_pattern(
                    cur_barcode,
                    rule.pattern,
                    rule.encoding
                );
                if (match.match) {
                    parsed_result.rule = rule;
                    break;
                }
            }
        }
    };

    // Extend parse_barcode to add rule information
    BarcodeParser.prototype.parse_barcode = function (barcode) {
        const parsed_result = originalParseBarcode.call(this, barcode);

        // Add rule information to the parsed result
        this._addRuleInformationToParsedResult(parsed_result, barcode);

        return parsed_result;
    };

    // Return something to satisfy the module system
    return BarcodeParser;
});
