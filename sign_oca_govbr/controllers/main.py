# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq

CALLBACK_PATH = "/sign_oca/govbr/callback"


class GovbrSignController(http.Controller):
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

    @staticmethod
    def _redirect_uri():
        return request.httprequest.url_root.rstrip("/") + CALLBACK_PATH

    @http.route(
        "/sign_oca/govbr/auth/<int:signer_id>/<string:access_token>",
        type="http",
        auth="public",
        website=False,
    )
    def govbr_auth(self, signer_id, access_token, **kwargs):
        signer = self._check_access(signer_id, access_token)
        return request.redirect(signer._govbr_authorization_url(self._redirect_uri()))

    @http.route(
        CALLBACK_PATH,
        type="http",
        auth="public",
        website=False,
        csrf=False,
    )
    def govbr_callback(self, **kwargs):
        state = kwargs.get("state")
        code = kwargs.get("code")
        if not state:
            return request.not_found()
        signer = (
            request.env["sign.oca.request.signer"]
            .sudo()
            .search([("govbr_state", "=", state)], limit=1)
        )
        if not signer:
            return request.not_found()
        url = signer.action_govbr_verify(code, state, self._redirect_uri())
        if not url:
            return request.redirect(signer.access_url)
        return request.redirect(url)
