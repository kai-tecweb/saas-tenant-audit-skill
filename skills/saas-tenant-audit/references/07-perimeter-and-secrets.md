# 07 — Perimeter, transport, debug exposure and secret hygiene

Contents: origin exposure · real client IP · headers and framing · debug/error output ·
internal endpoints · host-level access · secrets inventory · process supervisors ·
change safety

## Origin exposure (CDN/WAF bypass)

- Can the origin server be reached directly by IP, bypassing the CDN? Test from outside:
  connect to the origin address on 80/443 and on every app port (framework dev/prod
  ports, admin panels, database, cache). Probe only the named target hosts and a short list of well-known ports; no sweeps of address ranges. Anything reachable that should not be is a finding.
- Fix: firewall allow-list for the CDN ranges on 80/443, deny app ports; keep a documented
  procedure to refresh the ranges when the CDN publishes new ones. Keep SSH reachable by
  a method you can still use if keys are lost (see host access).
- Note that a framework's own public port may be blocked from SSRF by a port allow-list
  (`05`) but is still a direct-exposure issue.
- TLS mode: know whether CDN→origin is encrypted. Personal-data products should not send
  it in clear text; if an internal standard or vendor default says otherwise, record a
  reasoned exception rather than silently diverging. (Standards are defaults, not verdicts.)

## Real client IP (FL-20)

Rate limits and logs are only as good as the client IP. Before choosing a mechanism, list:

1. which headers each hop **sets** vs merely **passes through**;
2. whether the origin is reachable directly (then any header can be forged);
3. what the framework's "trusted proxy" option would trust.

The textbook "trust the forwarded-for header from localhost" is spoofable when the proxy
does not overwrite it or the origin is directly reachable. A safer pattern: trust only the
header that *your own proxy* writes from the socket peer address, and trust the CDN's
client-IP header only when that peer address is inside the CDN's published ranges; act only
when the immediate peer is loopback/private. Prove it with a before/after measurement
(stored IP was the proxy's; now the client's) and **one** request with forged headers
(stored IP must remain the true one). Normalise newlines when concatenating fetched range
lists and validate every entry.

Design consequence: if you later move the app runtime behind a different server, keep the
"peer is the local proxy" hop, or the trust logic breaks.

## Headers and framing (FL-27, FL-13)

- Transport security header on your own domains only (not on tenant custom domains you do
  not control); `nosniff`; a sane referrer policy; frame policy (`X-Frame-Options` or CSP
  `frame-ancestors`) — but remember earlier decisions constrain later features (an
  embeddable relay page must live on a host whose frame policy allows it).
- Remove or blank version banners (`Server`, `X-Powered-By`) at each hop; disable the
  language runtime's exposure flag too.
- Per-hostname behaviour: tenant sub-domains and custom domains often share one server
  block. A redirect or exact-match `location /` added for the marketing site can silently
  replace every tenant's root page. A status code proves reachability, not identity: check
  **content identity** (title/text unique to the tenant) for the apex, www, a tenant
  sub-domain and a custom domain. (FL-13)

## Debug and error output

- Debug mode must be off in production. **Verify with one harmless request** that
  triggers an error (bad route with a malformed parameter): a debug page discloses
  exception class, absolute paths, and stack traces. Agents/humans rate this differently;
  one confirming GET settles it. (FL-26)
- Production log level: check for debug-level logging of request bodies/tokens; rotate
  logs (daily with a retention window) so logs do not fill the disk or grow into a data
  store.
- Error responses for API clients should be generic and consistent.

## Internal-only endpoints

Endpoints intended for machine callers (cache revalidation, cron hooks, health/metrics,
framework build endpoints) should be unreachable from the internet: block at the reverse
proxy for external requests. **Before blocking, find every caller (FL-21)**, including your
own server calling itself through the public URL; switch those callers to an internal
address first, then block, then verify the internal path still works and the external one
is 403/404.

## Host-level access (only with explicit scope)

- SSH: key-only is ideal, but if password login is deliberately retained as a break-glass
  (e.g. no console access), document the reason and compensate: strong random password,
  fail2ban-style banning, no root login, low `MaxAuthTries`. Do **not** blindly
  recommend disabling it. Use `IdentitiesOnly` when many keys are loaded.
- `sudoers`: exact-match command lists, no wildcards; prove "passwordless" by running a
  harmless command with `sudo -n`, not by listing (`sudo -n -l` reports "allowed", which
  includes allowed-with-password). (FL-24)
- Privileged changes: keep one authenticated session open as a safety net, validate config
  before reload (`sshd -t`, `visudo -cf`, `nginx -t`), then confirm from a **new**
  connection before proceeding. One reviewed script per step, rollback stated first,
  verification by unprivileged reads. Say which machine, which account, and give absolute
  paths. (FL-32)

## Secret hygiene inventory

Only within the agreed scope and on systems you own or are authorised to inspect (never other people's files or accounts). Look for (report **counts, file names and key names only** — never values or matched
lines, FL-23):

- plaintext credentials in deploy scripts, docs, runbooks, shell history, CI config,
  editor settings/allow-lists, chat exports, AI-assistant memory/logs;
- `.env` backups and copies in the working tree that are **untracked but not ignored**
  (one commit away from publication) — compare by hash against the live file (FL-25);
- secrets that appear in git history (removal from HEAD is not rotation);
- the same value reused across services (system account, database root, other apps);
- file modes (`.env` should be 600), and who can read them;
- build-time public variables (`NEXT_PUBLIC_*`, `VITE_*`) that must be public — confirm no
  secret is in one (they are embedded in the bundle).

Rotation is complete only when the new value works, the old value is **refused everywhere
it might have worked**, and every place it was stored is cleaned. The agent doing the work
should not hold a secret it does not need: hand the user a one-line interactive command and
verify read-only afterwards. (FL-33)

## Process supervisors and "stopped" services (FL-22)

"Stop the app" often has several launch paths: process manager, cron/timers,
systemd units, container restart policies, deploy hooks. Find every supervisor, stop
each, wait one tick, and look again. Also check the deploy script's **health check**: it
may have been testing a different application than the one you think.

## Change safety

- Ports and process managers: when swapping the runtime (dev server → production
  app server), keep the address the proxy already uses, put the new runtime on a parallel
  port for side-by-side tests, cut over with an automatic rollback if the health check
  fails, and remove the old supervisor entry only after verification so a reboot cannot
  resurrect it and collide. (FL-35 notes)
- Measure the **limits you advertise** against the server that enforces them (upload
  caps, body sizes, timeouts); a development-server ini can silently cap far below the
  validation rule. (FL-35)
