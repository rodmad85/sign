# Configuration

1. Install `sign_oca` and `clinical_management` (this module depends on both).
2. Make sure each professional (`hr.employee`) has a linked portal user (or a
   work contact). The linked partner is used as the signer of the request.
3. Upload the handwritten signature image of the professional on the
   *Professional (Clinical)* tab of the employee form; it is printed on the
   clinical report layout (`clinical_management`).
4. Optionally install `sign_oca_certificate_digital` and/or `sign_oca_govbr`
   to require an authenticated signature before the document can be signed.
