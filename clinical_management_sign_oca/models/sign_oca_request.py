# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    clinical_report_id = fields.Many2one(
        comodel_name="hospital.clinical.report",
        compute="_compute_clinical_report_id",
        store=True,
        readonly=True,
        string="Clinical Report",
    )

    @api.depends("record_ref")
    def _compute_clinical_report_id(self):
        for item in self.filtered(
            lambda x: x.record_ref and x.record_ref._name == "hospital.clinical.report"
        ):
            item.clinical_report_id = item.record_ref.id

    def action_send_signed_request(self):
        result = super().action_send_signed_request()
        for sign_request in self:
            if (
                sign_request.state == "2_signed"
                and sign_request.clinical_report_id
                and sign_request.data
            ):
                sign_request.clinical_report_id.sudo().write(
                    {
                        "signed_document": sign_request.data,
                        "signed_document_filename": sign_request.name,
                        "state": "done",
                    }
                )
        return result
