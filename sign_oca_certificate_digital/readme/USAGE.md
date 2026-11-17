# Usage

The signer portal issues a challenge through
`/sign_oca/certificate/challenge/<signer_id>/<access_token>`. The signer signs
that challenge with the private key of the certificate and submits the PEM
certificate, the base64 signature and the challenge to
`/sign_oca/certificate/verify/<signer_id>/<access_token>`.

The endpoint returns `{"authenticated": true}` on success or
`{"authenticated": false, "error": "..."}` on failure. On success the signer
is marked as *Verified* and the usual Sign OCA signature flow is allowed to
continue. If the request requires this authentication and the signer is not
verified, `action_sign` is blocked.

The result is visible on the signer form under *Digital Certificate
Authentication*.
