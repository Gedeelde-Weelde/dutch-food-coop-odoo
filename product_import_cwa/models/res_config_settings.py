from odoo import api, fields, models

DEFAULT_PORTS = {"ftp": 21, "sftp": 22}


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    enable_ftp_import = fields.Boolean(
        "Enable CWA FTP Import", config_parameter="cwa_enable_ftp_import", default=False
    )
    cwa_import_method = fields.Selection(
        [("ftp", "FTP"), ("sftp", "SFTP")],
        "Import Method",
        config_parameter="cwa_import_method",
        default="ftp",
    )
    cwa_ftp_address = fields.Char(
        "FTP Address", config_parameter="cwa_ftp_address", default=""
    )
    cwa_ftp_port = fields.Integer(
        "Port", config_parameter="cwa_ftp_port", default=DEFAULT_PORTS["ftp"]
    )
    cwa_ftp_username = fields.Char(
        "Username", config_parameter="cwa_ftp_username", default=""
    )
    cwa_ftp_password = fields.Char(
        "Password", config_parameter="cwa_ftp_password", default=""
    )

    @api.onchange("cwa_import_method")
    def _onchange_cwa_import_method(self):
        # Only replace the port if it still holds a protocol default,
        # so a manually entered custom port is not clobbered.
        if self.cwa_ftp_port in (0, False, *DEFAULT_PORTS.values()):
            self.cwa_ftp_port = DEFAULT_PORTS.get(self.cwa_import_method, 21)
