# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError

CLINICAL_REPORT_XML_ID = "clinical_management.action_report_clinical_report"
SIGN_REQUEST_ACTION = "sign_oca.sign_oca_request_act_window"
SIGN_REQUEST_FORM = "sign_oca.sign_oca_request_form_view"
CLINICAL_ROLE = "clinical_management_sign_oca.sign_role_clinical_professional"

# Signature type -> (field on sign.oca.request, module that provides it).
# The fields are checked dynamically so the authentication modules stay
# independent from each other and are not a hard dependency of this glue.
# GOV.BR was removed from the professional's signature type: its API and
# Login Unico credentials are restricted to public-sector services
# (Portaria SGD/MGI 7.076/2024). The corresponding flag is kept here only
# to be explicitly turned off for image/certificate requests, in case the
# optional sign_oca_govbr module is installed with a company-wide default.
SIGNATURE_AUTH_REQUIREMENTS = {
    "certificate": (
        "require_certificate_authentication",
        "sign_oca_certificate_digital",
    ),
}
SIGNATURE_AUTH_FIELDS = (
    "require_certificate_authentication",
    "require_govbr_authentication",
)


class HospitalClinicalReport(models.Model):
    _inherit = "hospital.clinical.report"

    sign_request_ids = fields.One2many(
        comodel_name="sign.oca.request",
        inverse_name="clinical_report_id",
        string="Sign Requests",
    )
    sign_request_count = fields.Integer(
        string="Sign request count",
        compute="_compute_sign_request_count",
        store=True,
        compute_sudo=True,
    )
    signed_document = fields.Binary(
        string="Signed Clinical Report",
        attachment=True,
        copy=False,
    )
    signed_document_filename = fields.Char(copy=False)

    @api.depends("sign_request_ids")
    def _compute_sign_request_count(self):
        for report in self:
            report.sign_request_count = len(report.sign_request_ids)

    def _get_signature_partner(self):
        """Return the portal partner that must sign the clinical report."""
        self.ensure_one()
        professional = self.professional_id
        if not professional:
            raise ValidationError(
                self.env._("Please set the professional responsible for the report.")
            )
        partner = professional.user_id.partner_id or professional.work_contact_id
        if not partner:
            raise ValidationError(
                self.env._(
                    "The professional %(name)s has no linked user or work contact.",
                    name=professional.name,
                )
            )
        return partner

    def _professional_signature_type(self):
        """Return the professional's signature type (image on unknown values)."""
        self.ensure_one()
        if "signature_type" not in self.professional_id._fields:
            return "image"
        value = self.professional_id.signature_type or "image"
        if value in SIGNATURE_AUTH_REQUIREMENTS or value == "image":
            return value
        return "image"

    def _signature_auth_vals(self, signature_type, request_model):
        """Map the signature type to the Sign OCA authentication flags."""
        requirement = SIGNATURE_AUTH_REQUIREMENTS.get(signature_type)
        if requirement and requirement[0] not in request_model._fields:
            raise ValidationError(
                self.env._(
                    "Signature type '%(type)s' requires the '%(module)s' "
                    "module to be installed.",
                    type=signature_type,
                    module=requirement[1],
                )
            )
        vals = {}
        for field_name in SIGNATURE_AUTH_FIELDS:
            if field_name in request_model._fields:
                vals[field_name] = False
        if requirement:
            vals[requirement[0]] = True
        return vals

    def action_send_for_signature(self):
        """Render the clinical report PDF and create a Sign OCA request."""
        self.ensure_one()
        signature_type = self._professional_signature_type()
        if signature_type == "certificate" and not self.env.context.get(
            "skip_certificate_password"
        ):
            return self._action_certificate_password("sign")
        partner = self._get_signature_partner()
        role = self.env.ref(CLINICAL_ROLE, raise_if_not_found=False)
        if not role:
            raise ValidationError(
                self.env._("The 'Healthcare Professional' signature role is missing.")
            )
        report_action = self.env.ref(CLINICAL_REPORT_XML_ID)
        pdf, _content_type = (
            self.env["ir.actions.report"]
            .sudo()
            ._render_qweb_pdf(report_action.report_name, self.ids)
        )
        base_name = (self.name or "clinical_report").replace("/", "-")
        filename = f"{base_name}.pdf"
        request_model = self.env["sign.oca.request"]
        vals = {
            "name": self.name or filename,
            "filename": filename,
            "data": base64.b64encode(pdf),
            "record_ref": f"hospital.clinical.report,{self.id}",
            "user_id": self.env.user.id,
            "signer_ids": [
                Command.create({"role_id": role.id, "partner_id": partner.id})
            ],
        }
        vals.update(self._signature_auth_vals(signature_type, request_model))
        sign_request = request_model.create(vals)
        action = self.env["ir.actions.act_window"]._for_xml_id(SIGN_REQUEST_ACTION)
        action.update(
            {
                "views": [[self.env.ref(SIGN_REQUEST_FORM).id, "form"]],
                "res_id": sign_request.id,
            }
        )
        return action

    def action_view_sign_requests(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(SIGN_REQUEST_ACTION)
        action["domain"] = [("id", "in", self.sign_request_ids.ids)]
        action["context"] = dict(
            self.env.context,
            default_clinical_report_id=self.id,
            search_default_clinical_report_id=self.id,
        )
        return action
