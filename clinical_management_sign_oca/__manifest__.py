# Copyright 2026 Madooit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Clinical Management Sign Oca",
    "summary": "Electronic signature of clinical reports with Sign OCA",
    "version": "18.0.3.0.0",
    "license": "AGPL-3",
    "author": "Madooit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sign",
    "depends": ["sign_oca", "clinical_management"],
    "data": [
        "data/data.xml",
        "views/clinical_report_views.xml",
        "views/sign_oca_request_views.xml",
    ],
    "installable": True,
    "maintainers": ["rodmad85"],
}
