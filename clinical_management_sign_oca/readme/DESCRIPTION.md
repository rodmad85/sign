# Clinical Management Sign OCA

This module integrates **Sign OCA** with the clinical reports of
`clinical_management` (model `hospital.clinical.report`).

It allows the clinic to send a generated clinical report for electronic
signature, using the professional responsible for the report as the signer,
and stores the signed PDF back on the clinical report once every signer has
signed.

It follows the same integration pattern used by the OCA modules
`agreement_sign_oca`, `crm_sign_oca` and `project_task_sign_oca`.
