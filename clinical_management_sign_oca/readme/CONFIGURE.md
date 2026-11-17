# Configuration

1. Install `sign_oca` and `clinical_management` (this module depends on both).
2. Make sure each professional (`hr.employee`) has a linked portal user (or a
   work contact). The linked partner is used as the signer of the request.
3. Upload the handwritten signature image of the professional on the
   *Professional (Clinical)* tab of the employee form; it is printed on the
   clinical report layout (`clinical_management`).
4. Set the **Signature Type** on each professional (`clinical_management`):
   `Image` (default), `Digital Certificate` or `GOV.BR`. This module reads
   that choice when creating the sign request.
5. Install `sign_oca_certificate_digital` and/or `sign_oca_govbr` for the
   authenticated types. They are checked dynamically (no hard dependency),
   but if the matching module is missing the request is refused with a clear
   message instead of producing an unauthenticated document.
6. For `Digital Certificate`, register the A1 `.pfx/.p12` on the
   professional. The certificate password is requested on every emission by
   the `clinical_management` wizard and is never stored here.
