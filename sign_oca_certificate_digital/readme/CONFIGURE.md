# Configuration

Go to *Settings → Sign Oca → Digital Certificate Authentication*:

- **Require digital certificate authentication**: when enabled, every new
  sign request requires its signers to authenticate before signing. The
  requirement can still be toggled per request on the request form.
- **Certificate revocation endpoint**: optional URL of an OCSP/CRL gateway
  that receives `{"serial_number": "..."}` and returns
  `{"revoked": false}`. Leave it empty to skip the online revocation check.
