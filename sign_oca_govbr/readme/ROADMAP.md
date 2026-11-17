# Roadmap

- Validate the signed `id_token` (JWS) and the `nonce` against the stored
  value instead of relying only on the userinfo endpoint.
- Map the GOV.BR CPF to the partner's fiscal data and enforce the minimum
  reliability level (*selo prata/ouro*) per request.
