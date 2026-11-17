# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import re
import secrets
from datetime import datetime, timezone

import requests
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.x509.oid import NameOID

from odoo import fields, models
from odoo.exceptions import ValidationError

CPF_PATTERN = re.compile(r"\d{11}")
REQUEST_TIMEOUT = 10
ICP_REVOCATION_PARAM = "sign_oca_certificate_digital.revocation_url"


class SignOcaRequestSigner(models.Model):
    _inherit = "sign.oca.request.signer"

    certificate_auth_state = fields.Selection(
        [
            ("none", "Not authenticated"),
            ("pending", "Challenge issued"),
            ("verified", "Verified"),
            ("failed", "Failed"),
        ],
        string="Certificate Authentication",
        default="none",
        readonly=True,
        copy=False,
    )
    certificate_subject = fields.Char(readonly=True, copy=False)
    certificate_issuer = fields.Char(readonly=True, copy=False)
    certificate_serial_number = fields.Char(readonly=True, copy=False)
    certificate_cpf = fields.Char(readonly=True, copy=False)
    certificate_not_after = fields.Datetime(readonly=True, copy=False)
    certificate_verified_on = fields.Datetime(readonly=True, copy=False)
    certificate_challenge = fields.Char(readonly=True, copy=False)
    certificate_error = fields.Char(readonly=True, copy=False)

    def action_issue_certificate_challenge(self):
        """Create a random nonce the signer must sign with its private key."""
        self.ensure_one()
        challenge = secrets.token_urlsafe(32)
        self.write(
            {
                "certificate_challenge": challenge,
                "certificate_auth_state": "pending",
                "certificate_error": False,
            }
        )
        return challenge

    def action_certificate_authenticate(self, certificate_pem, signature, challenge):
        """Validate an X.509 certificate and the challenge it signed.

        Return ``True`` on success and ``False`` on failure. The failure reason
        is stored on the signer instead of being raised: Odoo rolls back the
        transaction when a ``UserError`` is raised, which would discard the
        audit data.
        """
        self.ensure_one()
        try:
            certificate = self._certificate_load(certificate_pem)
            self._certificate_check_validity(certificate)
            self._certificate_verify_challenge(certificate, signature, challenge)
            self._certificate_check_revocation(certificate)
        except (
            ValueError,
            TypeError,
            InvalidSignature,
            requests.RequestException,
        ) as error:
            self._certificate_fail(error)
            return False
        self.write(
            {
                "certificate_auth_state": "verified",
                "certificate_subject": certificate.subject.rfc4514_string(),
                "certificate_issuer": certificate.issuer.rfc4514_string(),
                "certificate_serial_number": str(certificate.serial_number),
                "certificate_cpf": self._certificate_extract_cpf(certificate),
                "certificate_not_after": self._certificate_not_after(certificate),
                "certificate_verified_on": fields.Datetime.now(),
                "certificate_error": False,
            }
        )
        return True

    def action_sign(self, items, access_token=False, latitude=False, longitude=False):
        self.ensure_one()
        if (
            self.request_id.require_certificate_authentication
            and self.certificate_auth_state != "verified"
        ):
            raise ValidationError(
                self.env._(
                    "A valid digital certificate authentication is required "
                    "before this document can be signed."
                )
            )
        return super().action_sign(
            items,
            access_token=access_token,
            latitude=latitude,
            longitude=longitude,
        )

    def _certificate_fail(self, error):
        self.ensure_one()
        message = str(error) or self.env._("Invalid certificate signature.")
        self.write(
            {
                "certificate_auth_state": "failed",
                "certificate_error": message,
            }
        )
        return True

    @staticmethod
    def _certificate_load(certificate_pem):
        if isinstance(certificate_pem, bytes):
            certificate_pem = certificate_pem.decode()
        return x509.load_pem_x509_certificate(certificate_pem.encode())

    def _certificate_check_validity(self, certificate):
        self.ensure_one()
        now = datetime.now(timezone.utc)
        not_before = getattr(certificate, "not_valid_before_utc", None)
        not_after = getattr(certificate, "not_valid_after_utc", None)
        if not_before is None:
            not_before = certificate.not_valid_before.replace(tzinfo=timezone.utc)
        if not_after is None:
            not_after = certificate.not_valid_after.replace(tzinfo=timezone.utc)
        if not (not_before <= now <= not_after):
            raise ValueError(
                self.env._("The certificate is outside its validity period.")
            )
        return True

    def _certificate_verify_challenge(self, certificate, signature, challenge):
        self.ensure_one()
        if not challenge or challenge != self.certificate_challenge:
            raise ValueError(self.env._("Invalid authentication challenge."))
        signature_bytes = base64.b64decode(signature)
        public_key = certificate.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(
                signature_bytes,
                challenge.encode(),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                signature_bytes,
                challenge.encode(),
                ec.ECDSA(hashes.SHA256()),
            )
        else:
            raise ValueError(self.env._("Unsupported certificate public key."))
        return True

    def _certificate_check_revocation(self, certificate):
        """Optional OCSP/CRL check; the external endpoint is mocked in tests."""
        self.ensure_one()
        url = self.env["ir.config_parameter"].sudo().get_param(ICP_REVOCATION_PARAM)
        if not url:
            return True
        response = requests.post(
            url,
            json={"serial_number": str(certificate.serial_number)},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        if response.json().get("revoked"):
            raise ValueError(self.env._("The certificate has been revoked."))
        return True

    @staticmethod
    def _certificate_extract_cpf(certificate):
        for attribute in certificate.subject:
            if attribute.oid == NameOID.SERIAL_NUMBER:
                match = CPF_PATTERN.search(attribute.value)
                if match:
                    return match.group()
        match = CPF_PATTERN.search(certificate.subject.rfc4514_string())
        return match.group() if match else False

    @staticmethod
    def _certificate_not_after(certificate):
        not_after = getattr(certificate, "not_valid_after_utc", None)
        if not_after is None:
            not_after = certificate.not_valid_after.replace(tzinfo=timezone.utc)
        return not_after.replace(tzinfo=None)
