# Configuration

Go to *Settings → Sign Oca → GOV.BR Authentication* and fill in the data of
your **Login Unico (GOV.BR)** integration:

- **Client ID** and **Client Secret** of the registered service.
- **Authorization endpoint**, **Token endpoint** and **Userinfo endpoint**
  of the GOV.BR OpenID Connect provider (use the endpoints documented for the
  environment of your integration).
- **Require GOV.BR authentication**: when enabled, every new sign request
  requires its signers to authenticate. The requirement can still be toggled
  per request on the request form.

Register `https://<your-odoo-host>/sign_oca/govbr/callback` as the allowed
redirect URI of the GOV.BR client.
