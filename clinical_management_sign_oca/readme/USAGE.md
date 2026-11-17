# Usage

Open a **Clinical Report** in *Draft* state and click **Request Signature**.

Odoo renders the report PDF and creates a `sign.oca.request` linked to the
report, with the responsible professional as signer and the
*Healthcare Professional* role. Configure the signature fields, send the
request and sign it from the portal.

The professional's **Signature Type** decides the request: with `Image` both
authentication flags are turned off (even if the company enables them by
default); with `Digital Certificate` or `GOV.BR` the corresponding flag is
turned on, so the signer must authenticate before signing. For the
certificate type, the A1 password wizard is shown first and the request is
only created after it is validated.

Once all signers have signed, the final PDF is copied to the **Signed Clinical
Report** field on the *Signature* tab and the report is set to *Done*. The
existing signature requests are reachable from the smart button on the report
form.
