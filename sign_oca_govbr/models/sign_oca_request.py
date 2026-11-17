# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

GOVBR_REQUIRE_PARAM = "sign_oca_govbr.require"


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    require_govbr_authentication = fields.Boolean(
        string="Require GOV.BR Authentication",
        default=lambda self: self._default_require_govbr_authentication(),
        help="Require the signer to authenticate with GOV.BR before the "
        "document can be signed.",
    )

    def _default_require_govbr_authentication(self):
        icp = self.env["ir.config_parameter"].sudo()
        return icp.get_param(GOVBR_REQUIRE_PARAM, "False") == "True"
