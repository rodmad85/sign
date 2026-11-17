# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime, timedelta, timezone
from io import BytesIO
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from reportlab.pdfgen import canvas

from odoo import Command
from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


def _build_pdf():
    stream = BytesIO()
    pdf_canvas = canvas.Canvas(stream)
    pdf_canvas.drawString(72, 720, "Clinical report")
    pdf_canvas.showPage()
    pdf_canvas.save()
    return stream.getvalue()


def _build_certificate(not_before=None, not_after=None):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "Dr. Test Professional"),
            x509.NameAttribute(NameOID.SERIAL_NUMBER, "12345678901"),
        ]
    )
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before or now - timedelta(days=1))
        .not_valid_after(not_after or now + timedelta(days=30))
        .sign(key, hashes.SHA256())
    )
    return key, certificate


class TestCertificateAuthentication(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Certificate Signer", "email": "cert@test.com"}
        )
        cls.role = cls.env.ref("sign_oca.sign_role_employee")
        cls.request = cls.env["sign.oca.request"].create(
            {
                "name": "Certificate test.pdf",
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
    def _sign_challenge(key, challenge):
        return base64.b64encode(
            key.sign(challenge.encode(), padding.PKCS1v15(), hashes.SHA256())
        )

    def _pem(self, certificate):
        return certificate.public_bytes(serialization.Encoding.PEM).decode()

    def test_certificate_authentication_success(self):
        key, certificate = _build_certificate()
        challenge = self.signer.action_issue_certificate_challenge()
        self.assertEqual(self.signer.certificate_auth_state, "pending")
        with patch.object(
            type(self.signer), "_certificate_check_revocation", return_value=True
        ):
            result = self.signer.action_certificate_authenticate(
                self._pem(certificate),
                self._sign_challenge(key, challenge),
                challenge,
            )
        self.assertTrue(result)
        self.assertEqual(self.signer.certificate_auth_state, "verified")
        self.assertEqual(self.signer.certificate_cpf, "12345678901")
        self.assertTrue(self.signer.certificate_verified_on)
        self.assertFalse(self.signer.certificate_error)

    def test_certificate_authentication_wrong_signature(self):
        _key, certificate = _build_certificate()
        other_key, _other_certificate = _build_certificate()
        challenge = self.signer.action_issue_certificate_challenge()
        with patch.object(
            type(self.signer), "_certificate_check_revocation", return_value=True
        ):
            result = self.signer.action_certificate_authenticate(
                self._pem(certificate),
                self._sign_challenge(other_key, challenge),
                challenge,
            )
        self.assertFalse(result)
        self.assertEqual(self.signer.certificate_auth_state, "failed")
        self.assertTrue(self.signer.certificate_error)

    def test_certificate_authentication_expired(self):
        key, certificate = _build_certificate(
            not_before=datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(days=60),
            not_after=datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(days=30),
        )
        challenge = self.signer.action_issue_certificate_challenge()
        result = self.signer.action_certificate_authenticate(
            self._pem(certificate),
            self._sign_challenge(key, challenge),
            challenge,
        )
        self.assertFalse(result)
        self.assertEqual(self.signer.certificate_auth_state, "failed")
        self.assertTrue(self.signer.certificate_error)

    def test_sign_requires_certificate_authentication(self):
        self.request.require_certificate_authentication = True
        with self.assertRaises(ValidationError):
            self.signer.action_sign({})

    def test_sign_allowed_after_authentication(self):
        self.request.require_certificate_authentication = True
        key, certificate = _build_certificate()
        challenge = self.signer.action_issue_certificate_challenge()
        with patch.object(
            type(self.signer), "_certificate_check_revocation", return_value=True
        ):
            self.signer.action_certificate_authenticate(
                self._pem(certificate),
                self._sign_challenge(key, challenge),
                challenge,
            )
        result = self.signer.action_sign({})
        self.assertTrue(self.signer.signed_on)
        self.assertTrue(result)
