# Entry-point inventory and two-tenant matrix

## Inventory (one row per method + path)

| # | Method | Path | Auth | Tenant derived from | IDs accepted (path / query / body / stored JSON) | State rule | Side effects | Cost | Limiter / quota | Denial convention |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GET | /api/v1/things/{id} | user | token | path | live only | none | none | – | 404 |

## Matrix (fill `actual` from the run; never from memory)

Fixtures: Tenant A (attacker) id=…, Tenant B (victim) id=…, control ID (never existed)=…
Baseline of B's data captured: yes/no (method: …)

| # | Actor | Target | Request | expected | actual | body shape | B changed? | Result |
|---|---|---|---|---|---|---|---|---|
| 1 | A | A (own) | GET /things/{A1} | 200 | | | n/a | control |
| 2 | A | B | GET /things/{B1} | 404 | | | n/a | |
| 3 | A | never | GET /things/{X} | 404 (== #2) | | | n/a | |
| 4 | anon | B | GET /things/{B1} | 401 | | | n/a | |
| 5 | A | B | PATCH /things/{B1} | 404 | | | yes/no | |
| 6 | A | A + B-ID in body | PATCH /things/{A1} {"parent_id": B1} | 404 or 422 (agreed) | | | yes/no | |

> Columns are examples. Use your resource's real states (for example draft/sent/paid/void/deleted) and record `409`/`422` where the product legitimately answers with a business-rule error. `expected` may list several acceptable codes (e.g. `404 or 422`, agreed with the owner).

## State x entry point (lifecycle)

| Entry point | live | draft | deleted | never existed |
|---|---|---|---|---|

## Summary
Pass: … Fail: … Not tested: … (reason)
