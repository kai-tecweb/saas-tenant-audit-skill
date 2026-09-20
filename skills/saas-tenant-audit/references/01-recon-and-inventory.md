# 01 — Recon and entry-point inventory

Goal: a complete table of *every* way to make the server do something, with the columns
you need to judge each one. Almost every serious finding in a real audit was an entry
point missing from someone's mental list. Build the list mechanically, not from memory.

## A. Where to get the list

**As an outside customer (black-box)**

1. Use the product like a customer with a browser and record network calls (HAR export or
   devtools). Note method, path, body shape, response shape.
2. Read the frontend's JavaScript bundle: search for the API base path, fetch/axios
   wrappers, and string literals that look like routes. One central API module is a gift;
   otherwise grep the chunks. Framework build output is public by design.
3. Public surfaces: `robots.txt`, `sitemap.xml`, machine-readable summaries, public JSON
   feeds, per-tenant public pages, embeddable widgets, webhook receivers (their existence
   is visible even if the secret is not).
4. Error and status behaviour: a 401 vs 404 vs 405 on a guessed path reveals whether a
   route exists (see existence oracles in `02`). Do not fuzz aggressively.
5. Response headers per hostname (CDN, framework, server), TLS/redirect behaviour on the
   apex, sub-domains and any tenant custom domains.

**With code/config access (second lens)**

- Laravel: `php artisan route:list --json` (method, URI, middleware). Note which routes
  lack an auth middleware, which lack a tenant/permission check, which are public POSTs.
- Next.js: `app/**/route.ts` handlers, Server Actions (each is a public POST endpoint),
  `middleware`/`proxy` matchers and rewrites, `next.config` headers/rewrites.
- Reverse-proxy config: which paths are forwarded where, what headers are set (real IP),
  what is *not* forwarded, whether the origin is reachable without the CDN.
- Scheduled jobs, queue jobs and webhooks: they act without a user session and are often
  forgotten. (FL-04)
- Every outbound call site (HTTP client, `curl`, file reads of URLs). (FL-15)
- Every paid-API call site (LLM, image, STT, SMS, e-mail). (FL-11, FL-16)

## B. The inventory table

One row per (method, path). Columns:

| Column | Meaning |
|---|---|
| Auth | none / user token / admin / signature (webhook) / secret header |
| Tenant scope | how the tenant is derived: from the token (good) or from a request field (must be validated) |
| IDs accepted | path params, query params, **and IDs inside JSON bodies or stored JSON fields** |
| State rule | which resource states are allowed (draft/published/deleted/expired) |
| Side effects | writes, e-mail, payment, AI call, file store, cache purge, queue job |
| Cost | none / cheap / paid per call |
| Rate/quota | limiter key (IP? user? tenant?), monthly cap, size cap |
| Denial convention | what a foreign or missing resource returns (e.g. 404 for both) |

Template: `templates/authz-matrix.md`.

## C. Classify each row

- **Public write** (anonymous POST): highest abuse exposure → phase 4.
- **ID-taking authenticated** (any `{id}`): cross-tenant exposure → phase 2.
- **State-bearing resource** (has a delete/publish/expire flag): → phase 3.
- **URL-taking** (server fetches or stores a user-supplied URL): → phase 5.
- **Token/credential/reset/webhook**: → phase 6.
- **Admin-only** (all-tenant data): check the admin gate on the route *and* on any data
  returned to non-admins. → phase 2.

## D. Reachability vs importance (FL-29)

A route with no UI caller is a fact about the code, not about the product. Record it, but
rank by reachability and real usage (row counts, logs) when prioritising *fixes*. Do not
drop it from the audit: backend-complete, UI-absent features are still attack surface,
and the missing UI often means nobody has tested them.

## E. Output

Hand the inventory to the user before continuing if it is large; unexpected rows
(forgotten admin routes, debug routes, old API versions) are findings on their own.
