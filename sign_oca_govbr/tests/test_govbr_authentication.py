# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from io import BytesIO
from unittest.mock import Mock, patch

from reportlab.pdfgen import canvas

from odoo import Command
from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon

MODULE = "odoo.addons.sign_oca_govbr.models.sign_oca_request_signer"
REDIRECT_URI = "https://odoo.test/sign_oca/govbr/callback"


def _build_pdf():
    stream = BytesIO()
    pdf_canvas = canvas.Canvas(stream)
    pdf_canvas.drawString(72, 720, "Clinical report")
    pdf_canvas.showPage()
    pdf_canvas.save()
    return stream.getvalue()


class TestGovbrAuthentication(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        icp = cls.env["ir.config_parameter"].sudo()
        icp.set_param("sign_oca_govbr.client_id", "test-client")
        icp.set_param("sign_oca_govbr.client_secret", "test-secret")
        icp.set_param("sign_oca_govbr.authorize_url", "https://gov.test/authorize")
        icp.set_param("sign_oca_govbr.token_url", "https://gov.test/token")
        icp.set_param("sign_oca_govbr.userinfo_url", "https://gov.test/userinfo")
        cls.partner = cls.env["res.partner"].create({"name": "GovBR Signer"})
        cls.role = cls.env.ref("sign_oca.sign_role_employee")
        cls.request = cls.env["sign.oca.request"].create(
            {
                "name": "GovBR test.pdf",
                "data": base64.b64encode(_build_pdf()),
                "state": "0_sent",
                "signer_ids": [
                    Command.create(
                        {"role_id": cls.role.id, "partner_id": cls.partner.id}
                    )
                ],
            }
        )
        cls.signer = cls.request.signer_ids

    @staticmethod
    def _mock_response(payload):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = payload
        return response

    def _verify(self):
        self.signer._govbr_authorization_url(REDIRECT_URI)
        state = self.signer.govbr_state
        with (
            patch(
                f"{MODULE}.requests.post",
                return_value=self._mock_response({"access_token": "test-token"}),
            ),
            patch(
                f"{MODULE}.requests.get",
                return_value=self._mock_response(
                    {"sub": "govbr-123", "cpf": "12345678901", "amr": ["pwd"]}
                ),
            ),
        ):
            return self.signer.action_govbr_verify("auth-code", state, REDIRECT_URI)

    def test_authorization_url(self):
        url = self.signer._govbr_authorization_url(REDIRECT_URI)
        self.assertTrue(url.startswith("https://gov.test/authorize?"))
        self.assertIn("client_id=test-client", url)
        self.assertIn("state=", url)
        self.assertTrue(self.signer.govbr_state)
        self.assertEqual(self.signer.govbr_auth_state, "pending")

    def test_govbr_authentication_success(self):
        url = self._verify()
        self.assertEqual(self.signer.govbr_auth_state, "verified")
        self.assertEqual(self.signer.govbr_cpf, "12345678901")
        self.assertEqual(self.signer.govbr_sub, "govbr-123")
        self.assertTrue(self.signer.govbr_verified_on)
        self.assertFalse(self.signer.govbr_state)
        self.assertEqual(url, self.signer.access_url)

    def test_invalid_state(self):
        self.signer._govbr_authorization_url(REDIRECT_URI)
        result = self.signer.action_govbr_verify(
            "auth-code", "wrong-state", REDIRECT_URI
        )
        self.assertFalse(result)
        self.assertEqual(self.signer.govbr_auth_state, "failed")
        self.assertTrue(self.signer.govbr_error)

    def test_sign_requires_govbr_authentication(self):
        self.request.require_govbr_authentication = True
        with self.assertRaises(ValidationError):
            self.signer.action_sign({})

    def test_sign_allowed_after_authentication(self):
        self.request.require_govbr_authentication = True
        self._verify()
        result = self.signer.action_sign({})
        self.assertTrue(self.signer.signed_on)
        self.assertTrue(result)
