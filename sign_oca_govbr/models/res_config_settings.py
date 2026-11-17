# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sign_oca_govbr_required = fields.Boolean(
        string="Require GOV.BR authentication",
        config_parameter="sign_oca_govbr.require",
        help="Require every new sign request to authenticate its signers "
        "with GOV.BR.",
    )
    sign_oca_govbr_client_id = fields.Char(
        string="GOV.BR Client ID",
        config_parameter="sign_oca_govbr.client_id",
        help="Client ID of the Login Unico (GOV.BR) integration.",
    )
    sign_oca_govbr_client_secret = fields.Char(
        string="GOV.BR Client Secret",
        config_parameter="sign_oca_govbr.client_secret",
        help="Client secret of the Login Unico (GOV.BR) integration.",
    )
    sign_oca_govbr_authorize_url = fields.Char(
        string="GOV.BR authorization endpoint",
        config_parameter="sign_oca_govbr.authorize_url",
        help="Authorization endpoint of the GOV.BR OpenID Connect provider.",
    )
    sign_oca_govbr_token_url = fields.Char(
        string="GOV.BR token endpoint",
        config_parameter="sign_oca_govbr.token_url",
        help="Token endpoint used to exchange the authorization code.",
    )
    sign_oca_govbr_userinfo_url = fields.Char(
        string="GOV.BR userinfo endpoint",
        config_parameter="sign_oca_govbr.userinfo_url",
        help="Userinfo endpoint used to read the authenticated CPF.",
    )
