# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import secrets
from urllib.parse import urlencode

import requests

from odoo import fields, models
from odoo.exceptions import ValidationError

REQUEST_TIMEOUT = 10
GOVBR_SCOPE = "openid profile email phone cpf"
PARAM_PREFIX = "sign_oca_govbr."


class SignOcaRequestSigner(models.Model):
    _inherit = "sign.oca.request.signer"

    govbr_auth_state = fields.Selection(
        [
            ("none", "Not authenticated"),
            ("pending", "Waiting for GOV.BR"),
            ("verified", "Verified"),
            ("failed", "Failed"),
        ],
        string="GOV.BR Authentication",
        default="none",
        readonly=True,
        copy=False,
    )
    govbr_state = fields.Char(readonly=True, copy=False)
    govbr_sub = fields.Char(readonly=True, copy=False)
    govbr_cpf = fields.Char(readonly=True, copy=False)
    govbr_trust_level = fields.Char(readonly=True, copy=False)
    govbr_amr = fields.Char(readonly=True, copy=False)
    govbr_verified_on = fields.Datetime(readonly=True, copy=False)
    govbr_error = fields.Char(readonly=True, copy=False)

    def _govbr_param(self, name):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(f"{PARAM_PREFIX}{name}", "")
        )

    def _govbr_authorization_url(self, redirect_uri):
        """Start the OIDC flow and return the GOV.BR authorize URL."""
        self.ensure_one()
        client_id = self._govbr_param("client_id")
        authorize_url = self._govbr_param("authorize_url")
        if not client_id or not authorize_url:
            raise ValidationError(
                self.env._("The GOV.BR integration is not configured.")
            )
        state = secrets.token_urlsafe(32)
        self.write(
            {
                "govbr_state": state,
                "govbr_auth_state": "pending",
                "govbr_error": False,
            }
        )
        params = {
            "response_type": "code",
            "client_id": client_id,
            "scope": GOVBR_SCOPE,
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": secrets.token_urlsafe(16),
        }
        return f"{authorize_url}?{urlencode(params)}"

    def _govbr_exchange_code(self, code, redirect_uri):
        """Exchange the authorization code for an access token (mockable)."""
        self.ensure_one()
        token_url = self._govbr_param("token_url")
        if not token_url:
            raise ValueError(self.env._("The GOV.BR token endpoint is not configured."))
        response = requests.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self._govbr_param("client_id"),
                "client_secret": self._govbr_param("client_secret"),
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("access_token")

    def _govbr_fetch_userinfo(self, access_token):
        """Read the authenticated identity from GOV.BR (mockable)."""
        self.ensure_one()
        userinfo_url = self._govbr_param("userinfo_url")
        if not userinfo_url:
            raise ValueError(
                self.env._("The GOV.BR userinfo endpoint is not configured.")
            )
        response = requests.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def action_govbr_verify(self, code, state, redirect_uri):
        """Validate the OIDC callback and record the signer identity.

        Return the signer portal URL on success and ``False`` on failure.
        Failures are stored on the signer instead of being raised, because
        Odoo rolls back the transaction when a ``UserError`` is raised.
        """
        self.ensure_one()
        try:
            if not state or state != self.govbr_state:
                raise ValueError(self.env._("Invalid GOV.BR authentication state."))
            access_token = self._govbr_exchange_code(code, redirect_uri)
            if not access_token:
                raise ValueError(self.env._("GOV.BR did not return an access token."))
            userinfo = self._govbr_fetch_userinfo(access_token)
            self._govbr_check_userinfo(userinfo)
        except (ValueError, TypeError, requests.RequestException) as error:
            self._govbr_fail(error)
            return False
        self.write(
            {
                "govbr_auth_state": "verified",
                "govbr_sub": str(userinfo.get("sub")),
                "govbr_cpf": str(userinfo.get("cpf")),
                "govbr_trust_level": str(userinfo.get("trust_level") or ""),
                "govbr_amr": str(userinfo.get("amr") or ""),
                "govbr_verified_on": fields.Datetime.now(),
                "govbr_error": False,
                "govbr_state": False,
            }
        )
        return self.access_url

    def _govbr_check_userinfo(self, userinfo):
        self.ensure_one()
        if not userinfo.get("sub"):
            raise ValueError(self.env._("GOV.BR did not return the subject (sub)."))
        if not userinfo.get("cpf"):
            raise ValueError(self.env._("GOV.BR did not return the signer CPF."))
        return True

    def _govbr_fail(self, error):
        self.ensure_one()
        message = str(error) or self.env._("GOV.BR authentication was rejected.")
        self.write(
            {
                "govbr_auth_state": "failed",
                "govbr_error": message,
                "govbr_state": False,
            }
        )
        return True

    def action_sign(self, items, access_token=False, latitude=False, longitude=False):
        self.ensure_one()
        if (
            self.request_id.require_govbr_authentication
            and self.govbr_auth_state != "verified"
        ):
            raise ValidationError(
                self.env._(
                    "A valid GOV.BR authentication is required before this "
                    "document can be signed."
                )
            )
        return super().action_sign(
            items,
            access_token=access_token,
            latitude=latitude,
            longitude=longitude,
        )
