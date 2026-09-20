# 08 — Concurrency, limits and quotas

"It's in a transaction" and "it's a single statement" are not evidence. A concurrency fix
is verified when **the broken version visibly breaks under the same test**. (FL-17)

## Which primitive for which claim

| Claim | Primitive | Notes |
|---|---|---|
| "at most N" (consume exactly 1) | one conditional `UPDATE ... SET used = used + n WHERE used + n <= limit`; success = 1 affected row | ensure the counter row exists *before* (outside) the transaction |
| "grant up to N of what is left" | row lock (`SELECT ... FOR UPDATE`) inside a transaction, compute `min(N, limit - used)` | ensure the row exists first: an `INSERT IGNORE` on an existing row takes a shared lock, and doing it inside the same transaction as the exclusive lock invites a deadlock |
| "only one worker processes this" | conditional update to a claimed state; or a per-resource non-overlapping job lock that does not release back to the queue | also make the job re-read the resource state |
| "merge into a JSON document from two writers" | row lock + read-modify-write, or write only keys that are still empty | naive read-modify-write loses updates |
| "unique across tenants" | database unique index (not an application pre-check) | pre-checks race |

Engine notes: the same primitives exist elsewhere. PostgreSQL: `INSERT ... ON CONFLICT DO NOTHING` to ensure the row, `UPDATE ... WHERE used + n <= limit` for the conditional consume, `SELECT ... FOR UPDATE` for locks (the isolation level changes what a re-read sees). Redis: an atomic `INCR` with a Lua script or `SET NX` for claims.

Counters: increment in the guard; refund **only** on failure of the guarded action; do not
decrement on delete.

## Verification recipe

For each fix, run against a scratch tenant on the real database engine:

1. **Parallel run** — N concurrent requests against a limit of L (N > L). Expect exactly L
   successes.
2. **Naive control** — the old implementation (or a deliberately unlocked variant) under
   the *same* test. It must show lost updates or over-grants. If it does not, your test
   cannot detect the bug.
3. **Report both numbers** ("12 parallel vs limit 5 → 5 succeeded; control → 9").
4. Repeat "grant up to N" style with N larger than what is left and confirm a partial grant.
5. Check **no duplicate side effects**: exactly one e-mail, one vendor call, one row.

## Scaling assumptions (FL-17)

Adding replicas silently invalidates assumptions that only held with one instance. Before
scaling workers, list every timeout/lease/lock TTL and compare:

- queue `retry_after`/visibility timeout must be **greater than the longest job timeout**,
  otherwise a running job is redelivered to another worker (duplicate execution). Prove
  with a job longer than the old value whose `attempts` stays 1.
- job overlap locks and unique locks; scheduler `onOneServer`; cache-based locks on a
  non-shared cache.
- any in-process cache or static state used as a lock or counter.

Encode the comparison as a unit test that reflects over the job classes.

## Read-then-act traps (TOCTOU) worth probing

- "Count existing items, then create" for plan limits (parallel requests exceed the
  limit by the parallelism).
- "Check balance/quota, then call vendor, then record" (record first or reserve first).
- "Verify then use" for tokens/links (single-use must be enforced by the delete/update,
  not by a prior read).
- Session creation caps per identifier.

## Load-test hygiene

Tens of requests, scratch tenant, no vendor calls (or a stubbed path), and clean up
counters and rows afterwards. Your own rate limiter may throttle the test — clear counters
between sections or use fresh keys. (FL-09)
