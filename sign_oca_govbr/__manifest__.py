# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sign Oca Gov.BR Authentication",
    "summary": "Authenticate signers with GOV.BR (Login Unico OIDC)",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Madooit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": ["sign_oca"],
    "data": [
        "views/sign_oca_request_views.xml",
        "views/sign_oca_request_signer_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "maintainers": ["rodmad85"],
}
