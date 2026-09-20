# 03 — Lifecycle and state invariants

Authorization asks **"whose is it?"**. Lifecycle asks **"is it still alive?"** An audit
needs both questions on every entry point. (FL-04)

## The recurring shape of the bug

A resource has a state flag: soft-deleted, unpublished/draft, expired, suspended, archived.
The team implements the flag on the first few read paths. Entry points added later (form
submit, chat, booking, payment, embed, export, webhook, scheduled job) copy the *lookup*
(`status = published`) but not the *invariant* (`not deleted`). Result: "deleted and still
public" is the normal state of every deleted item, and each late entry point keeps
working — accepting form data, sending owner e-mail, taking payments, spending AI money.

## Procedure

1. **List the states** of each resource type and the legal transitions.
2. **Build a table** — rows: every entry point (authenticated and public, read and write,
   jobs, webhooks, sitemap/feeds, caches); columns: each state. Mark what the entry point
   does in each cell. Empty or "works" cells for a dead state are findings.
3. **Test the property "indistinguishable from a resource that never existed"** — for a
   deleted (or unpublished) resource, every entry point must answer exactly like it does
   for an ID/slug that was never created. Do not assert a literal `404` from assumption:
   some endpoints legitimately answer `200 {"data": null}` for "not configured". Compare
   with the control. (FL-04, FL-06)
4. **Run the real flow, not a DB edit**: create → configure → publish → delete, then
   probe every public entry point and confirm caches drop the item within seconds.
5. **Check asynchronous actors**: queued jobs and scheduled tasks must re-read state at
   execution time and abort (no vendor call, no e-mail) if the resource is gone. Enqueue a
   job, delete the resource, let the job run, and confirm no side effect.
6. **Check every cache and derived surface**: page cache/ISR, sitemap, machine-readable
   summaries (`llms.txt`-style files), search indexes, CDN, group/menu documents that
   reference the resource. A passing check on the dynamic route says nothing about the
   pre-rendered one — test each consumer separately. (FL-04)
7. **Make the delete operation close the door itself**: on delete, also unpublish,
   detach from groups/menus, purge caches, and clear public tokens. Then a forgotten entry
   point fails safe instead of open.
8. **Identifier reuse**: can a deleted resource's public identifier (slug, subdomain,
   short link) be re-registered by someone else? Reuse enables impersonation and hijack
   of old links/search results. Prefer a quarantine period before release.
9. **Backfill**: after the fix, find existing rows already in the bad state (deleted and
   published) and correct them.

## Expiry and suspension variants

- Trial/plan expiry, suspended tenants, revoked tokens, past-due billing: same table,
  same "does every entry point respect it?" question.
- An external event that flips a tenant to `past_due` must be scoped to that tenant
  (see the null-guard lesson in `06`).

## Reachability caveat (FL-29)

Before ranking fixes, check if the affected feature has a UI entry point and real usage
(row counts, logs). The bug is still real, but "urgent" vs "irrelevant" changes with
reachability. Do not use this to skip the audit of unreachable but exposed endpoints.

## Example table (abbreviated)

| Entry point | live | draft | deleted | never existed |
|---|---|---|---|---|
| GET public page | 200 | 404 | **404** | 404 |
| POST public form | 200 | 404 | **200 (bug)** | 404 |
| POST public payment | 200 | 404 | **200 (bug)** | 404 |
| sitemap listing | listed | absent | absent | absent |
| queued export job | runs | aborts | **runs (bug)** | n/a |
