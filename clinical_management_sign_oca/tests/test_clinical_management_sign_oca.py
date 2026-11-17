# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon

DUMMY_PDF = b"%PDF-1.4\n% test clinical report\n"


class TestClinicalManagementSignOca(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.signer_user = new_test_user(
            cls.env,
            login="test-clinical-signer",
            groups="sign_oca.sign_oca_group_user,base.group_user",
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Dr. Test Professional",
                "user_id": cls.signer_user.id,
                "professional_title": "Fonoaudiologo",
            }
        )
        cls.patient = cls.env["res.partner"].create(
            {
                "name": "Test Patient",
                "tipo": "paciente",
                "professional_ids": [(6, 0, cls.employee.ids)],
            }
        )
        cls.report = cls.env["hospital.clinical.report"].create(
            {
                "report_type": "report",
                "patient_id": cls.patient.id,
                "professional_id": cls.employee.id,
                "report_date": "2026-01-01",
                "content": "<p>Clinical content.</p>",
            }
        )
        cls.role = cls.env.ref(
            "clinical_management_sign_oca.sign_role_clinical_professional"
        )

    def _create_request(self, **kwargs):
        vals = {
            "name": "Signed Clinical Report.pdf",
            "data": base64.b64encode(DUMMY_PDF),
            "record_ref": f"hospital.clinical.report,{self.report.id}",
            "state": "0_sent",
            "signer_ids": [
                Command.create(
                    {
                        "role_id": self.role.id,
                        "partner_id": self.signer_user.partner_id.id,
                    }
                )
            ],
        }
        vals.update(kwargs)
        return self.env["sign.oca.request"].create(vals)

    def test_action_send_for_signature(self):
        self.assertEqual(self.report.sign_request_count, 0)
        with patch.object(
            type(self.env["ir.actions.report"]),
            "_render_qweb_pdf",
            return_value=(DUMMY_PDF, "pdf"),
        ):
            action = self.report.action_send_for_signature()
        request = self.env["sign.oca.request"].browse(action["res_id"])
        self.assertEqual(action["views"][0][1], "form")
        self.assertEqual(request.record_ref, self.report)
        self.assertEqual(request.clinical_report_id, self.report)
        self.assertEqual(request.data, base64.b64encode(DUMMY_PDF))
        self.assertEqual(len(request.signer_ids), 1)
        self.assertEqual(request.signer_ids.partner_id, self.signer_user.partner_id)
        self.assertEqual(request.signer_ids.role_id, self.role)
        self.assertEqual(self.report.sign_request_count, 1)

    def test_action_send_for_signature_without_professional(self):
        self.report.professional_id = False
        with self.assertRaises(ValidationError):
            self.report.action_send_for_signature()

    def test_action_view_sign_requests(self):
        request = self._create_request()
        action = self.report.action_view_sign_requests()
        self.assertIn(request.id, action["domain"][0][2])

    def test_signed_document_stored_back(self):
        request = self._create_request()
        for signer in request.signer_ids:
            signer.signed_on = "2026-01-01 10:00:00"
        request.state = "2_signed"
        request.action_send_signed_request()
        self.assertEqual(self.report.signed_document, request.data)
        self.assertEqual(self.report.signed_document_filename, request.name)
        self.assertEqual(self.report.state, "done")

    def test_signed_document_not_stored_when_unsigned(self):
        request = self._create_request()
        request.action_send_signed_request()
        self.assertFalse(self.report.signed_document)
        self.assertEqual(self.report.state, "draft")

    def _send_for_signature(self):
        """Create a request bypassing the (clinical_management) password gate."""
        report = self.report.with_context(skip_certificate_password=True)
        with patch.object(
            type(self.env["ir.actions.report"]),
            "_render_qweb_pdf",
            return_value=(DUMMY_PDF, "pdf"),
        ):
            return report.action_send_for_signature()

    def test_certificate_signature_opens_password_wizard(self):
        self.employee.signature_type = "certificate"
        action = self.report.action_send_for_signature()
        self.assertEqual(action["res_model"], "hospital.certificate.password.wizard")
        self.assertEqual(action["context"]["default_next_action"], "sign")
        self.assertEqual(action["context"]["default_report_id"], self.report.id)

    def test_image_signature_disables_auth_flags(self):
        self.employee.signature_type = "image"
        action = self._send_for_signature()
        request = self.env["sign.oca.request"].browse(action["res_id"])
        fields = self.env["sign.oca.request"]._fields
        if "require_certificate_authentication" in fields:
            self.assertFalse(request.require_certificate_authentication)
        if "require_govbr_authentication" in fields:
            self.assertFalse(request.require_govbr_authentication)

    def test_certificate_signature_enables_certificate_auth(self):
        self.employee.signature_type = "certificate"
        fields = self.env["sign.oca.request"]._fields
        if "require_certificate_authentication" not in fields:
            with self.assertRaises(ValidationError):
                self._send_for_signature()
            return
        action = self._send_for_signature()
        request = self.env["sign.oca.request"].browse(action["res_id"])
        self.assertTrue(request.require_certificate_authentication)
        if "require_govbr_authentication" in fields:
            self.assertFalse(request.require_govbr_authentication)

    def test_signature_type_excludes_govbr(self):
        """GOV.BR is not offered to a private clinic (public-sector API)."""
        selection = dict(self.env["hr.employee"]._fields["signature_type"].selection)
        self.assertNotIn("govbr", selection)
        self.assertIn("certificate", selection)
