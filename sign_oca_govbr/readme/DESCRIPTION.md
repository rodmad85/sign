# Sign OCA GOV.BR Authentication

Complementary authentication provider for **Sign OCA**.

It authenticates the signer with **GOV.BR (Login Unico)** using the OpenID
Connect authorization-code flow: the signer is redirected to GOV.BR, the
`state`/`nonce` are validated on the callback, the authorization code is
exchanged for an access token and the identity (`sub`, CPF and trust level) is
read from the userinfo endpoint and recorded on the signer.

All HTTP calls go through `requests` with an explicit timeout and are mocked
in the tests, so the module can be installed and tested without real GOV.BR
credentials.
