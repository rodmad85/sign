# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sign_oca_certificate_required = fields.Boolean(
        string="Require digital certificate authentication",
        config_parameter="sign_oca_certificate_digital.require",
        help="Require every new sign request to authenticate its signers with "
        "an ICP-Brasil digital certificate.",
    )
    sign_oca_certificate_revocation_url = fields.Char(
        string="Certificate revocation endpoint",
        config_parameter="sign_oca_certificate_digital.revocation_url",
        help="Optional HTTP endpoint of an OCSP/CRL gateway used to check "
        "certificate revocation. Leave empty to skip the online check.",
    )
