# Usage

From the signer portal, open
`/sign_oca/govbr/auth/<signer_id>/<access_token>` to start the authentication.
GOV.BR redirects back to `/sign_oca/govbr/callback`, which validates the
`state`, exchanges the code and records the signer identity.

On failure the callback returns to the signer page without marking the
signer as verified, and the reason is stored on the signer. When the request
requires GOV.BR authentication and the signer is not verified, `action_sign`
is blocked with a clear error. The authentication result is visible on the
signer form under *GOV.BR Authentication*.
