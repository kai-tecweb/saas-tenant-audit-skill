# 02 — Two-tenant black-box matrix (the core of the audit)

Contents: setup · the matrix · what to vary · existence oracles · IDs hiding in data ·
admin gates · pass/fail rules · triple-lens rule · example row

## Setup

- Create **Tenant A** (attacker) and **Tenant B** (victim), each with one user, using the
  product's normal sign-up path. If sign-up is protected (CAPTCHA, e-mail verification),
  create them the way the owner allows and *say so*; do not bypass protections on the
  public path just to save time.
- Give B a full set of fixtures, one per relevant state: a normal resource, a
  published/public one, a draft, a soft-deleted one, one with children (nested
  resources), one with an uploaded file, one with an external link/URL field, and any
  billing/plan object the product has.
- Record B's IDs and a **snapshot of B's data** (row counts and a hash or dump of the
  fixture rows). You will compare it after every write-type probe.
- Get a session/token for A. Also keep an unauthenticated client and, if the product has
  them, a low-privilege user in A's tenant.
- Add a **control**: an ID that never existed (same shape as real IDs).
- **Snapshot method.** If you own the scratch environment, snapshot B's rows in the database. With customer-level access only (pure black-box), snapshot through the API: read B's own list/detail endpoints *as B* before and after and compare. Say which method you used; an API-only snapshot cannot see fields the API hides.

## The matrix

For every inventory row that takes an ID or acts on a tenant resource, run:

| Actor | Target | Expected |
|---|---|---|
| A (valid token) | A's own resource | success (positive control — proves the request is well-formed) |
| A | B's resource | the product's denial convention (e.g. 404) |
| A | never-existed ID | **same response as the line above** |
| anonymous | B's resource (protected route) | 401 |
| A (non-admin) | admin-only route | 403 (or the convention) |
| B's low-privilege user | B's owner-only route | 403 |

Print each line as `METHOD path | actor | expected=<code> actual=<code> | body-shape`.
After every write/delete-type probe, diff B's snapshot. A denied request that still
changed B's data is a critical finding even if the status looked right. (FL-06)

Agree the **denial convention** with the owner first (usually 404 for "not yours" so
existence is not revealed). Test for the convention, not merely for "no data returned".
(FL-03)

## What to vary on every row

1. **Path IDs** — swap in B's IDs.
2. **Query parameters** — `?id=`, `?tenant=`, `?owner=`, filters, includes, sort keys.
3. **JSON body fields** — every ID-looking field: `parent_id`, `template_id`,
   `resource_ids[]`, `owner_id`, `tenant_id`, nested arrays and stored JSON blobs (e.g. a
   menu or layout document that lists IDs of other resources). (FL-02)
4. **Mass assignment** — send extra fields that should be server-controlled
   (`tenant_id`, `status`, `is_admin`, `price`, quota counters). Check the response *and*
   the stored row. (FL-11, stack notes)
5. **Bulk/list endpoints** — do they filter by tenant, or by tenant *and* state? Do
   pagination/cursors or search leak other tenants' rows or counts?
6. **Nested routes** — `/parents/{p}/children/{c}`: is `c` verified to belong to `p`
   *and* `p` to the tenant? Mismatched pairs are a classic gap.
7. **Different verbs on the same path** — GET is scoped, PATCH/DELETE is not (or the
   reverse). Also HEAD/OPTIONS and old API versions.
8. **Uploads and downloads** — can A fetch B's stored file by guessing the path? Are
   file URLs unguessable and are they authenticated where they should be?
9. **Cross-resource side channels** — exports, invoices, webhooks, audit logs, search
   suggestions, analytics, notifications.
10. **Public endpoints that resolve IDs** — an anonymous endpoint that dereferences IDs
    stored in a tenant's data can leak *other* tenants' metadata (FL-02).
11. **Capability URLs (secret links)** — pages or downloads protected only by an unguessable token in the URL (pay links, share links, password-reset links, signed file URLs). Check: token length/entropy and that it is not derived from a sequential ID; expiry and revocation; that deleting or voiding the resource kills the link; that the response is not cached publicly by the CDN; that the token does not leak through `Referer` or logs.

## Existence oracles (FL-03)

An attacker learns that a resource exists if any of these differ between "not found" and
"not yours":

- status code (404 vs 403 vs 200-with-null),
- response body or error message, response *shape*,
- response time (extra lookups),
- an early return such as "already recorded → success" placed **before** the ownership
  check,
- different validation errors (422 on a foreign ID means the ID was looked up).

Compare foreign-ID and never-existed-ID responses byte-for-byte (status, body shape,
headers of note). They should be indistinguishable.

## IDs hiding in data (FL-02)

Review every field that *stores* references to other resources: layout/menu documents,
"related items", saved filters, share lists, workflow steps. Two questions each:

1. On **write**: does the server verify every referenced ID belongs to the caller's
   tenant? (A sibling endpoint being scoped does not prove this one is.)
2. On **read**, especially anonymous read: does the server re-check tenant and state
   (published, not deleted) when it resolves those IDs?

## Admin and role gates

- Every route that returns all-tenant data needs an explicit admin gate. Test it with A's
  ordinary token; also test the admin *UI* data source (it may call ordinary routes that
  are missing the gate).
- Check impersonation/"view as" and support tooling.
- A role flag that can be set through profile update or sign-up is a privilege
  escalation (mass assignment).

## Pass/fail rules

- Fail on any of: B's data returned; B's data changed; different responses for foreign vs
  never-existed IDs (unless the owner accepted a different convention); success for A on
  an admin route; success without authentication where 401 is expected.
- A row is "not tested" (and must be listed in the report) if a positive control could
  not be produced.
- Every failure gets re-run once after a clean rebuild of fixtures to exclude harness
  error before it becomes a finding. (FL-06, FL-10)

## The triple-lens rule (FL-01)

Reading each handler for a tenant filter found only part of the gaps in the field. The
rest were found by (a) an independent second reviewer told to re-scan "every method that
takes an ID" with a *different framing*, and (b) this black-box matrix with before/after
snapshots. Use all three: static read, independent re-scan, live matrix. See
`12-orchestration.md`.

## Example row (generic)

```
PATCH /api/v1/projects/{id}/items/{itemId}
  A→own/own      expected=200 actual=200 shape=ok           (control)
  A→B/B          expected=404 actual=404 shape=notfound     PASS
  A→A/B-item     expected=404 actual=200 shape=ok           FAIL: item not tied to parent  (B snapshot changed: yes)
  A→never/never  expected=404 actual=404 shape=notfound     control matches B row
```
