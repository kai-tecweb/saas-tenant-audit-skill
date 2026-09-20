# 04 — Public-endpoint abuse, cost and rate limiting

Contents: threat model · inventory of cost surfaces · controls checklist · bot protection ·
embeddable widgets · quotas · how to test without side effects · what limits do not stop

Anonymous and free-tier endpoints can be turned into: a mail relay, a paid-API meter
(LLM, image, speech), a storage filler, a card-testing oracle, or a way to mass-create
trial accounts. The fix is layered; the audit checks each layer exists **and has been seen
to say no**. (FL-11)

## 1. Find every cost and side-effect surface

From the inventory (`01`), mark each endpoint that, without the caller paying, can:

- send e-mail/SMS (contact forms, sign-up confirmation, password reset, invitations,
  owner notifications) — the recipient may be attacker-chosen;
- call a paid vendor (LLM, image generation, speech-to-text, maps, search);
- create durable data or files (submissions, uploads, sessions, accounts, trials);
- touch payments (create intents, apply coupons, verify purchases);
- enqueue heavy jobs.

Also inspect **authenticated free-tier** users: a verified account is not a paid account.

- **Payment and import integrity** (if the product has them): amounts and currency reconciled server-side against your own records; a replay window and a live/test-mode check on payment events; size limits and formula-injection neutralisation (cells starting with `=`, `+`, `-`, `@`) for spreadsheet import/export; archive and upload bombs.

## 2. Controls checklist (per surface)

| Control | Check | Field note |
|---|---|---|
| Rate limit keyed to the **real client IP** | Does the limiter see the true client, or every request as the proxy's address? | FL-20 |
| Composite keys where useful | login: identifier+IP; also consider a per-IP ceiling so one IP cannot spray many identifiers | FL-16 |
| Human/bot check on anonymous writes | server-side verification, **fail-closed** on vendor outage/misconfig; token single-use and bound to an action | FL-14 |
| Per-tenant monthly quota for paid calls | atomic counter incremented by the guard itself; released only on failure | FL-11, FL-17 |
| Verified e-mail before paid features | gate on verification, not just login | — |
| Input size caps | characters per field, JSON size, array counts, upload bytes; validate *before* the paid call | — |
| Per-session/per-conversation caps | for chat-like features: turns per session, sessions per IP | — |
| Recipient caps | number of notification recipients, no user-controlled `To`/`Cc`/`Bcc` | — |
| Idempotency/dup guards | repeated identical submissions | — |
| Retry/queue safety | jobs are single-flight per resource; `retry_after` > longest job timeout | FL-17 |
| Kill switch | a per-feature off switch that takes effect immediately, including cached pages | — |

## 3. Bot protection specifics (FL-14)

- The server must **verify the token itself**, not trust the client. Missing, invalid,
  reused, or wrong-action token → reject (422/403). Vendor unreachable or secret missing →
  **reject** (fail-closed, 503) rather than allow.
- Apply the limiter *before* the vendor call so garbage tokens cannot be used to hammer
  the vendor.
- Test both paths deliberately:
  - failure path: no token, fake token, reused token, token from another action;
  - success path: only with a real browser session. Automation-launched browsers are
    often (correctly) rejected by the widget; attach to a normally launched browser over
    a debugging port to exercise the happy path.
- Widgets often render inside shadow DOM/iframes: assert on the hidden response input
  rather than on the iframe selector.
- Widgets are domain-bound. Tenant **custom domains** may not be allowed for the widget;
  a relay page on an allowed host with strict parent-origin checking (`postMessage` to the
  exact parent origin, nonce, `frame-ancestors` for registered domains only) solves it
  without loosening the check. Read your earlier headers first: a frame-denial policy
  decides where a relay page can live. (FL-27)
- Ordering: the widget must reset after each submit (tokens are single-use).
- Use the vendor's documented test keys in non-production environments where they exist, and only ever test widgets that belong to the target you are authorized to audit.

## 4. Embeddable widgets and cross-origin use (FL-27)

For a widget that tenants embed (chat, booking, forms):

- Bind the created session to the **origin** it was issued for and reject other origins
  with the same response as "not found".
- Only serve resources that are enabled, published/not deleted, *and referenced by the
  page that embeds them* — a bare ID must not be enough. Otherwise any site (or curl) can
  use another tenant's widget on that tenant's bill.
- State the limit honestly: non-browser clients can forge `Origin`. The origin check stops
  other *sites* using your tenants' widgets; bot verification, throttles and quotas stop
  scripts. The resource ID in a public page is public information; do not rely on hiding
  it.

## 5. Quotas: design and verification

- Count in a table keyed (tenant, counter, period) and consume with **one conditional
  UPDATE** (`used + n <= limit`) for "at most N"; use a row lock for "grant up to N of what
  is left". Ensure the row exists *outside* the transaction. (FL-17)
- Decrement only for failed attempts, never on delete, or delete-and-recreate defeats the
  cap.
- Before hardening an existing limit, **prove the old one ever counted**: hit it past the
  limit on a scratch tenant and read the stored numbers back. A cap that sums a column
  which is silently dropped by mass-assignment protection is unlimited. (FL-11)
- Test with parallel requests plus a naive control (see `08`).

## 6. Test without side effects (FL-16)

- Trip rate limiters via **non-existent targets** (404 after the limiter counted, before
  any mail/AI/payment call).
- Use unique fake identifiers per test so real accounts are never locked out.
- Measure recovery by waiting past `Retry-After` for minute-scale limiters; for
  hour-scale ones, move the stored expiry into the past to simulate natural expiry, then
  delete the keys.
- Delete every counter, cache key and row created (including rows created asynchronously
  by jobs). Compare with the baseline.
- **Your own harness is subject to the limiter**: clear counters between sections, and
  remember that clearing a shared cache table can also wipe sessions your test needs.
  (FL-09)
- Some of these steps (moving a stored expiry into the past, deleting counters or cache keys, reading counters) need database or host access to your scratch environment. With customer-level access only, use the product's own delete/reset endpoints and fresh identifiers, and list what could not be cleaned or verified.

## 7. What these controls do not stop (say it in the report)

- Per-IP limits: shared NAT/CGNAT buckets, distributed sources, IPv6 (group by /64).
- Origin checks: non-browser clients can forge the header.
- Monthly caps: they bound cost, not abuse *within* the cap; alerting/notification when a
  cap is reached is a separate control (notify once per period, not per event).
- Bot checks: paid human solvers exist; they raise cost, they do not eliminate abuse.
