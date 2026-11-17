# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq


class CertificateSignController(http.Controller):
    @staticmethod
    def _check_access(signer_id, access_token):
        signer = (
            request.env["sign.oca.request.signer"].sudo().browse(signer_id).exists()
        )
        if (
            not signer
            or not signer.access_token
            or not consteq(signer.access_token, access_token or "")
        ):
            raise AccessError(request.env._("Invalid signature access token."))
        return signer

    @http.route(
        "/sign_oca/certificate/challenge/<int:signer_id>/<string:access_token>",
        type="json",
        auth="public",
        website=True,
    )
    def certificate_challenge(self, signer_id, access_token):
        signer = self._check_access(signer_id, access_token)
        return signer.action_issue_certificate_challenge()

    @http.route(
        "/sign_oca/certificate/verify/<int:signer_id>/<string:access_token>",
        type="json",
        auth="public",
        website=True,
    )
    def certificate_verify(
        self, signer_id, access_token, certificate_pem, signature, challenge
    ):
        signer = self._check_access(signer_id, access_token)
        authenticated = signer.action_certificate_authenticate(
            certificate_pem, signature, challenge
        )
        return {"authenticated": authenticated, "error": signer.certificate_error}
