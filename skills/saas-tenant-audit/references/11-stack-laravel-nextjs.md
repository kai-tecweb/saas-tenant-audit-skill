# 11 — Stack notes: Laravel API + Next.js frontend, multi-tenant SaaS

Contents: tenancy model checks · Laravel · Sanctum · Next.js · the seam between them ·
multi-tenant specifics · quick probes

Provenance tags: **[field]** observed in the campaign, **[std]** standard framework
knowledge. Everything else in this skill is stack-agnostic.

## Tenancy model checks (any stack)

- The tenant must come from the **authenticated identity** (token → user → tenant), never
  from a request field. A client-supplied tenant id is at most a *selector* that must be
  checked against the identity. [std]
- Put the tenant in every lookup, **cache key**, rate-limit key, queue payload and
  file path; re-establish tenant context inside queue consumers/scheduled jobs. [std]
- Uniqueness (slugs, sub-domains, custom domains, names) is enforced per the intended
  scope with database unique indexes, not application pre-checks. [std]
- Public identifiers (slug, sub-domain) have a reuse policy (`03`). [field]

## Laravel

- **Inventory**: `php artisan route:list --json`; read the middleware column. [std]
- **Scoped finder**: one helper (`findForTenantOrFail($id, $tenantId)`) used by every
  handler beats per-handler `where('tenant_id', …)`; it also enforces the 404 convention.
  [field] Prefer a global scope or policy where it fits, but verify the black-box result;
  scopes are bypassed by `withoutGlobalScopes`, raw queries, joins and `DB::table`.
- **Route model binding** without scoping fetches any tenant's row by id; scope it
  (`scopeBindings`, custom `resolveRouteBinding`) or don't bind. [std]
- **Validation rules that hit the database** (`exists:`, `unique:`) are not
  tenant-scoped by default; `exists:items,id` proves the row exists somewhere, not that
  it is the caller's. [std] This is also an existence oracle (422 vs 404).
- **Mass assignment** [field/std]: check `$fillable`/`$guarded` for both directions:
  (a) privileged columns (tenant, role, status, quota counters) must not be fillable from
  request input; (b) columns the *code* writes must be fillable, or the write is silently
  dropped (a quota that "counts" a never-written column is unlimited). Prefer
  `$request->validated()` over `$request->all()`.
- **Soft deletes and status** [field]: `is_deleted`-style flags are not `SoftDeletes`;
  check every finder (public, jobs) applies the invariant; a reusable scope
  (`scopeLive`) helps.
- **Queues/jobs** [field]: jobs re-read state at execution; `retry_after` > longest job
  `timeout`; overlap middleware for per-resource jobs; with several workers, verify no
  duplicate execution.
- **Rate limiting** [field]: named limiters with explicit keys (identifier+IP;
  IP only for public writes; user for authenticated). Custom throttle responses should
  return the same JSON shape the client reads. Limiter state in the database cache means a
  deploy that clears the cache also clears counters (and sessions if they share the store).
- **Real client IP** [field]: a global middleware that acts only when the peer is
  loopback/private, trusts the proxy-written header, and trusts the CDN header only from
  the CDN's ranges. Avoid `trustProxies('*')`. Refresh the CDN range list on a schedule.
- **Passwords** [field]: `Password::defaults()` with min length + uncompromised check;
  tune the breached-password client timeout; apply on register/change/reset only.
- **Config cache** [std]: after changing `.env`, `config:clear` then `config:cache`;
  `env()` outside config files returns null when config is cached.
- **Debug** [field]: `APP_DEBUG=false`; check the error page with one malformed request.
- **Logging** [field]: `daily` channel with a retention window; no request bodies or
  tokens at debug level in production.
- **Regex** [field]: `\z` instead of `$` for full-string anchors in PHP.
- **HTTP client**: outbound calls only through the guarded fetcher (`05`); ban raw
  `Http::`/`curl` for user-influenced URLs in code review.
- **Mail**: no user-controlled recipients; queue mail; a fake address on a reserved domain
  in tests.

## Sanctum / API tokens [field]

- Per-token `expires_at` (new tokens only) vs global `expiration` (retroactive) — FL-19.
- Does login revoke all tokens (single session)? Know before designing revocation tests.
- Password change and reset: revoke other tokens. E-mail change: require current password.
- Bearer tokens contain `|`; never `source` them in shell fixtures. (FL-07)
- Prune expired tokens on a schedule (`sanctum:prune-expired`).
- Admin gate: a dedicated middleware on all-tenant routes; abilities on admin tokens.

## Next.js

- **Route handlers (`route.ts`) are public HTTP endpoints** unless you protect them.
  [field: an unauthenticated cache-revalidation handler] Require a shared secret (503 if
  unset, 403 on mismatch), validate input strictly, call it server-to-server only, and
  block it from the internet at the proxy (`07`).
- **Server Actions are public POST endpoints**: authenticate and authorize *inside* each
  action; treat arguments as hostile; do not rely on the page being hidden. [std]
- **Middleware/proxy is not your only authorization layer.** Keep the framework patched
  (a widely-published middleware-bypass CVE let a crafted internal header skip middleware)
  and re-check access in the data layer. [std]
- **Build-time public variables** (`NEXT_PUBLIC_*`) are embedded in the bundle: fine for a
  CAPTCHA site key, never for secrets; changing one needs a rebuild. [field]
- **Rewrites/proxying to the API**: know which headers the proxy sets (real IP) and that
  the API must not trust client-supplied copies. [field]
- **ISR / caching**: after publish, unpublish, delete, slug change, domain change — is the
  cache invalidated for *every* consumer (page, sitemap, feed, machine-readable summary)?
  Test each. [field] Different consumers (dynamic vs prerendered) fail independently.
- **Host-based routing (custom domains)**: the app maps `Host` → tenant. Verify unknown
  hosts, hosts of deleted tenants, and unregistered hosts trying to embed your pages
  (frame-ancestors) fail closed. Never take the tenant from a client header. [field]
- **XSS**: `dangerouslySetInnerHTML`, rich-text fields, URL fields (`javascript:` scheme),
  markdown renderers, third-party embed HTML. Allow-list URL schemes. [std/field]
- **Images**: client-side resizing before upload reduces size but is not validation —
  the server enforces type/size/dimensions; strip EXIF metadata if privacy matters.
  [field/std]
- **Error/redirect handling**: 401 → redirect to login is a UI path to test.
- **CORS, CSRF and token storage** [std]: a permissive CORS policy plus cookie auth is a cross-site risk; token in `localStorage` is readable by any XSS. Check the API's CORS allow-list, cookie flags (`Secure`, `HttpOnly`, `SameSite`) and whether state-changing routes need a CSRF defence.
- **CDN caching of per-tenant or authenticated pages** [std]: confirm `Cache-Control`/`Vary` so one tenant's response is never served to another; check that source maps and debug routes are not public.

## The seam between Laravel and Next.js [field]

- The two halves are deployed separately: a change that requires both (new secret header,
  new required field) needs an order that leaves no window (`10`, FL-21).
- Internal calls (Next → API, API → Next) should use internal addresses; external routes to
  them should be blocked.
- Shared secrets live in both environment files (mode 600); rotate both together and
  restart in the order the dependency requires.

## Multi-tenant SaaS specifics

- Billing state is per tenant; webhook handlers must resolve the tenant from a verified
  external id and no-op if it cannot (FL-28).
- Plan limits: enforced server-side, both count limits (items per plan) and monthly
  quotas; parallel creation can exceed count limits by the concurrency (`08`).
- Public tenant pages, widgets and forms are the anonymous attack surface: apply `04`.
- Admin/support tooling: separate gate, audit trail, no tenant-switch via request field.
- Data export/deletion requests: define retention and what disappears from public surfaces.

## Quick probes (black-box, safe)

```
# unauthenticated access to every protected route → expect 401
# tenant A token on tenant B ids → expect the agreed denial (404)
# A token on never-existed id → identical to the line above
# public write endpoint with a non-existent target, a dozen times in a row → 429 on the limiter's count
# public endpoint for a deleted/unpublished resource → identical to never-existed
# webhook endpoint with no/forged signature → 4xx; with signature from an empty secret → 4xx
# malformed request to trigger an error page → generic response, no stack trace
# origin address directly on 80/443 and app ports → refused/timeout
```

## Porting to other stacks

The method is stack-agnostic; only the lookup commands change. Starting points (verify against current docs):

| Need | Laravel | Django / DRF | Rails | Express / Nest | Spring |
|---|---|---|---|---|---|
| Route inventory | `route:list --json` | `show_urls` / router registry, viewsets | `rails routes` | router tree / decorators | mappings via Actuator or code search |
| Tenant-scoped finder | one helper + scopes | `get_queryset()` filtered by tenant | `default_scope` / `acts_as_tenant` | repository method with tenant arg | `@PreAuthorize` + tenant-aware repository |
| Mass assignment | `$fillable` / `validated()` | serializer `fields` / `read_only_fields` | strong parameters | DTO whitelist | DTO binding |
| Token expiry | per-token `expires_at` | token model has no expiry by default: add it | Devise/JWT settings | JWT `exp` + revocation list | JWT/session settings |
| Background jobs | queue `retry_after` | Celery visibility timeout | Sidekiq retries | BullMQ lock duration | scheduler/lock config |

For row-level tenancy check every query path; for schema-per-tenant check how the schema is selected and reset per request/job. Add a stack note file for your stack in the same style (provenance tags **[field]**/**[std]**) and keep the English and Japanese copies in sync.
