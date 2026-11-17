# Sign OCA Digital Certificate Authentication

Complementary authentication provider for **Sign OCA**.

It verifies the identity of a signer with an ICP-Brasil X.509 digital
certificate before the electronic signature is accepted: the certificate
validity is checked, the signer proves possession of the private key by
signing a random challenge, and certificate data (subject, issuer, serial
number, CPF and expiration) is recorded for auditing.

The optional online revocation check (OCSP/CRL gateway) is the only external
service used and is fully mockable, so the module can be installed and tested
without real certificates or credentials.
