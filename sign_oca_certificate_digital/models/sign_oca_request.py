# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

ICP_REQUIRE_PARAM = "sign_oca_certificate_digital.require"


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    require_certificate_authentication = fields.Boolean(
        string="Require Digital Certificate Authentication",
        default=lambda self: self._default_require_certificate_authentication(),
        help="Require the signer to authenticate with an ICP-Brasil X.509 "
        "certificate before the document can be signed.",
    )

    def _default_require_certificate_authentication(self):
        icp = self.env["ir.config_parameter"].sudo()
        return icp.get_param(ICP_REQUIRE_PARAM, "False") == "True"
