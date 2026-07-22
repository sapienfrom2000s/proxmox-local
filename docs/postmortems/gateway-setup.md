# Gateway Setup Postmortem

## What happened

Setting up TLS termination and routing for homelab services via Gateway API. Two
issues encountered during the process.

---

## Issue 1: Cross-namespace routing blocked

**Symptom:** 500 Internal Server Error from NGINX Gateway Fabric. The NGINX
config showed `proxy_pass http://invalid-backend-ref`.

**Root cause:** The HTTPRoute was in the `gateway` namespace, but the backend
service (`todo-api`) was in the `todo` namespace. Gateway API blocks
cross-namespace backend references by default for security.

**Fix:** Created a ReferenceGrant in the `todo` namespace allowing the HTTPRoute
from `gateway` to reference services in `todo`.

```
  HTTPRoute (gateway ns) ──references──► Service (todo ns)
                     │                       │
                     │   ReferenceGrant      │
                     └───── allows this ─────┘
```

**Lesson:** Always create a ReferenceGrant when HTTPRoute and backend service
are in different namespaces.

---

## Issue 2: Wildcard certificate not matching

**Symptom:** Safari and curl rejected `*.home` matching `todo.home`. Firefox
threw `SEC_ERROR_BAD_SIGNATURE`.

**Root cause:** Two separate problems:

1. Safari/curl with SecureTransport have known issues with wildcard SAN
   matching. The cert had `DNS:*.home` but clients didn't match it to
   `todo.home`.

2. Firefox has its own certificate store, separate from macOS Keychain. Even
   though the root CA was trusted system-wide, Firefox didn't see it.

**Fix:**

1. Added `todo.home` explicitly to the certificate's dnsNames list
2. Imported the root CA into Firefox's cert store separately

**Lesson:** Don't rely on wildcard matching alone. Add explicit hostnames to
certificate SANs. Each browser may have its own trust store.

---

## Issue 3: Firefox HTTPS not working

**Symptom:** Firefox showed `SEC_ERROR_BAD_SIGNATURE` — "Peer's certificate has
an invalid signature." Safari and curl worked after fixing Issue 2.

**Root cause:** Firefox maintains its own certificate authority store,
completely separate from macOS Keychain. Even though the root CA was added to
Keychain (which fixed Safari and system curl), Firefox never saw it.

**Fix:** Import the root CA into Firefox's own trust store:

1. Firefox → Settings → Privacy & Security → Certificates → View Certificates
2. Authorities tab → Import → select `home-ca.crt`
3. Check "Trust this CA to identify websites"

**Lesson:** Each browser manages trust independently. macOS Keychain is not
shared with Firefox. Chrome/Safari use Keychain; Firefox and some Linux browsers
maintain their own stores.
