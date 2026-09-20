# 09 — Field lessons: test-harness and audit pitfalls

Contents: how to read this file · index · A. Test design · B. Test-data hygiene ·
C. Tooling and environment · D. Authorization-audit method · E. Security-design lessons ·
F. Operations and hand-offs

These entries come from mistakes that were **actually made** during a real audit-and-fix
campaign on a multi-tenant SaaS and were caught only because of counts, exact status codes
or independent review. They are abstracted: no names, hosts or data. Provenance tags:
**[field]** = observed in the campaign; **[std]** = standard practice reinforced by it.
Read sections A and B *before* writing any verification script.

How to use it: the **Symptom** lines are concrete examples from one campaign (a specific
framework, token format or language quirk); each **Do** line is stack-agnostic — apply the
Do, not the anecdote. Section F (operations) matters most when you also operate the
servers; skip it for a purely managed-hosting target. Each lesson comes from one campaign:
treat them as strong hints, not as proof of frequency.

## Index

| Id | One-line lesson |
|---|---|
| FL-01 | Reading `where(tenant)` in a handler is not proof of isolation — use three lenses |
| FL-02 | IDs hide in JSON bodies and stored fields, not only in URLs |
| FL-03 | Existence oracles: status, shape, early returns, timing |
| FL-04 | State (deleted/unpublished) is an invariant at every entry point, job and cache |
| FL-05 | Cleanup: raw output, prefix-based, independent of setup, baseline equality |
| FL-06 | Print expected next to actual; assert the exact status |
| FL-07 | Assert the precondition; keep fixtures out of shell `source` |
| FL-08 | Every absence check needs a positive control |
| FL-09 | Your traffic is subject to the target's defenses (limits, sessions, cache) |
| FL-10 | A stale regression script gives a wrong verdict |
| FL-11 | Test the existing control before improving it |
| FL-12 | Test tooling masquerades as product bugs (UA blocks, enums, double runs) |
| FL-13 | A status code proves reachability, not that the right content was served |
| FL-14 | Bot-protection: test the failure path; automation browsers are rejected |
| FL-15 | SSRF has more sinks than the named one |
| FL-16 | Test limits without side effects — and say what they do not stop |
| FL-17 | Concurrency claims need a control group and the right primitive |
| FL-18 | Fail closed on missing config; test the characters the author forgot |
| FL-19 | Choose the security switch whose blast radius matches the requirement |
| FL-20 | Trust a header only if the hop that wrote it cannot be impersonated |
| FL-21 | Find every caller before closing a path; order paired client/server deploys |
| FL-22 | "Stopped" means no launch path remains |
| FL-23 | A leaked secret is valid wherever it was typed; never quote matches |
| FL-24 | `sudo -n -l` cannot prove "passwordless" |
| FL-25 | Untracked, un-ignored secret backups in the working tree |
| FL-26 | Agents rate the same finding differently — the orchestrator verifies |
| FL-27 | Earlier hardening constrains later features; state each control's limit |
| FL-28 | External APIs move fields — null-guard updates keyed by external ids |
| FL-29 | Reachability changes priority, not existence |
| FL-30 | Exercise the real feature path, not a database shortcut |
| FL-31 | When the local runtime lacks an extension, test on the real host |
| FL-32 | Hand-offs: name the machine, account, absolute path, rollback first |
| FL-33 | Never carry a secret you do not need |
| FL-34 | Kill by PID, never by a pattern that can match yourself |
| FL-35 | Measure the limits you advertise against the server that enforces them |

---

## A. Test design

### FL-06 Print expected next to actual; assert the exact status [field]
- **Symptom:** a script reported "blocked" for a request that should have been 404 but was
  429 (the limiter caught the harness); another passed 403 checks with empty bodies because
  authorization runs before validation.
- **Why:** "some refusal happened" is true for many wrong reasons.
- **Do:** one line per request: `label | expected=404 actual=404`. Assert positives too
  (`allowed → 200/201`, not merely "not 403"). Use keyword arguments or a helper that
  validates request bodies; positional helpers get swapped silently.

### FL-07 Assert the precondition [field]
- **Symptom:** a revocation test printed `before: 401 401 / after: 401 401` and looked
  like success. The "before" was wrong: the state file holding bearer tokens was
  `source`d and tokens contain `|`, and an intermediate login revoked every token
  (single-session app).
- **Do:** assert `before == expected` and fail loudly. Store fixtures as JSON or with
  `printf %q`, never via `source`. List helpers that mutate shared state (login, logout,
  refresh) before ordering steps. Learn the app's session model first.

### FL-08 Every absence check needs a positive control [field]
- **Symptom:** "no duplicate e-mail was queued" printed True — because the test had wiped
  its own sessions, so the request never reached the code under test.
- **Do:** in the same line as the negative result, assert the triggering step ran (exact
  status/code). Treat a negative result as unproven until the positive control passes.

### FL-10 A stale regression script gives a wrong verdict [field]
- **Symptom:** after an infrastructure change, an old end-to-end script was re-run as a
  regression check. It failed everywhere, because the product's contract had changed since
  (a required header), and it also wrote a spurious ERROR into the production log.
- **Do:** before reuse, diff the script's assumptions against the current contract; prefer
  the newest script covering the area; note in the report which log lines the tests
  themselves produced.

### FL-11 Test the existing control before improving it [field]
- **Symptom:** a monthly usage cap on a paid feature was about to be hardened against races. Reading
  back the stored numbers showed the counted column was always 0 (mass-assignment protection
  silently dropped it), so the old cap had never limited anything.
- **Do:** first hit the *existing* guard past its limit on a scratch tenant and read the
  stored numbers. Prefer a counter incremented by the guard itself over a sum over logs
  written elsewhere. Treat "column exists but is not writable via the model" as a smell.

### FL-30 Exercise the real feature path [field]
- **Symptom:** a database edit "worked", while going through the product's own gated flow
  exposed a production-wide webhook bug (`FL-28`).
- **Do:** prefer the real path; a shortcut succeeds regardless of hidden preconditions.

---

## B. Test-data hygiene

### FL-05 Cleanup that cannot hide failure [field]
- **Symptom (three times):** cleanup and setup steps were piped through `grep` for a marker
  line. A fatal database error produced *empty output* that looked like "nothing to report";
  setup failed halfway, cleanup handled organizations but not users; a foreign key blocked
  a delete and nothing said so. Leftover rows were found only by a baseline count.
- **Do:**
  1. Print **raw** output of setup and cleanup. Never `| grep`, never `2>/dev/null` there.
  2. Assert setup returned non-empty IDs before proceeding.
  3. Clean by **prefix in every table the setup touches** (including foreign-key owners such
     as history tables, async writers such as job-created rows, caches and throttle
     counters), independent of what setup actually created.
  4. Run cleanup at the **start** as well as the end (a killed or hung run leaves fixtures).
  5. End with a **baseline-equality** check (counts per table before == after) and fail if
     not equal.
  6. Compare counts on the test-owned subset when other actors share the database.

### FL-09 Your traffic is subject to the target's defenses [field]
- **Symptom:** harness requests tripped the per-IP limiter and reported 429 where 404 was
  expected; clearing a shared cache table to reset counters also deleted the login sessions
  the test needed, so later steps failed for the wrong reason.
- **Do:** plan limiter windows into the run; reset per section; know what else lives in the
  store you reset and re-create it; use fresh identifiers where possible; run suites
  spaced past rate-limit windows.

### FL-12 Tooling masquerades as product bugs [field]
- **Symptom:** the CDN answered 403 to the HTTP library's default User-Agent; a seeded row
  used an invalid enum value; running the suite twice within a minute tripped a limiter; a
  stale test user from the previous step skewed counts.
- **Do:** use a browser-like UA and note it; validate fixtures against the schema; snapshot
  counts before every run and treat any mismatch as leftovers from earlier steps.

### FL-34 Kill by PID, never by a pattern that can match yourself [field]
- **Symptom (twice):** a process-kill pattern also matched the shell command line carrying
  it and killed the session; a helper server started with the language's built-in server
  left forked workers alive after killing the parent.
- **Do:** capture the PID at start (`$!`) and kill that; match binaries by full path; after
  cleanup check that the listening port is closed. When a slip repeats, replace the rule
  with a tool that makes it impossible (a wrapper script), not a reminder.

---

## C. Tooling and environment

### FL-14 Testing bot-protection widgets [field]
- Automation-launched browsers (headless or driven) are often correctly rejected by the
  widget (challenge failure error code). A normally launched browser attached over a remote
  debugging port passes. The vendor's **error codes** separate "misconfigured (hostname not
  registered)" from "detected as automation".
- The widget's iframe is in shadow DOM — assert on the hidden response input field.
- Test the **failure path** as deliberately as the success path: missing, fake, reused,
  wrong-action tokens; vendor outage (must fail closed).

### FL-31 When the local runtime lacks an extension [field]
- The local PHP lacked the HTTP extension and some XML/DOM/mbstring extensions, so the real
  test runner and real client could not run. A homemade runner must mimic the runner's
  isolation rules (fresh application per test) or it hides state-leak bugs; pin/abort
  behaviour of the real client must be verified on the real host in a scratch harness.

### FL-35 Measure the limits you advertise [field]
- A migration plan prompted measuring the *current* upload cap: the development server's
  runtime setting allowed far less than validation advertised, so ordinary uploads had been
  failing silently. Test each advertised limit against the layer that actually enforces it
  (proxy body size, runtime setting, framework validation), and pick migrations that keep those
  hidden contracts intact.

---

## D. Authorization-audit method

### FL-01 Three lenses (static read, independent re-scan, live matrix) [field]
- A route-by-route read of the whole authenticated API found most of the gaps; a few more were
  found only by an independent reviewer told to re-scan "every method that takes an ID", and by
  a live two-tenant matrix comparing the victim's data before/after.
- **Do:** run all three. Frame the second reviewer differently from the first.

### FL-02 IDs in JSON bodies and stored fields [field]
- A layout document accepted arbitrary resource IDs; the sibling "add item" endpoint was
  scoped, so it *looked* covered, and an anonymous read resolved those IDs without tenant
  or published filtering — a cross-tenant metadata leak through a data field.
- **Do:** treat every stored reference as an input to be verified on write and re-verified
  on read.

### FL-03 Existence oracles [field]
- "Already recorded → success" ran before the ownership check; "not found" vs "not yours"
  returned different statuses; scoped queries returned `200 null` where the agreed
  convention was 404.
- **Do:** agree the denial convention and test for it; compare foreign-ID and never-existed
  responses.

### FL-04 State is an invariant at every entry point [field]
- Soft-delete left `status='published'`, so every late-added public write endpoint (form
  submission, booking, payment, ...) kept working for deleted items.
- **Do:** the state × entry-point table (`03`); make delete close the door; check jobs and
  caches; express the invariant relative to a control ("indistinguishable from never
  existed") — one endpoint legitimately returned `200 null` for "not configured" and the
  first expectation (404) was wrong. A green result on one cache consumer says nothing
  about the others (dynamic route vs pre-rendered sitemap). A test that writes to a shared
  cache must clean the cache too.

### FL-29 Reachability changes priority, not existence [field]
- Before ranking, check UI entry points and real usage. A feature with a complete API but no
  UI caller is real surface but a different priority. An inventory should say which layer
  each claim rests on (route exists / UI wires it / has real usage).

### FL-13 A status code proves reachability, not correctness [field]
- A "do links still work?" check looked only at HTTP status while a proxy change had
  replaced every tenant's root page with the marketing site. Verify content identity for
  anything meant to differ per tenant; treat exact-match paths as shared by every host.

### FL-26 Agents rate the same finding differently [field]
- Parallel read-only audit agents rated one finding at different severities; only one harmless
  confirming request settled it. Read-only briefs also caused agents to skip recording lessons.
- **Do:** the orchestrator verifies each candidate with one minimal request; do not average
  ratings. Say in the brief who records observations and that agents should report
  candidates instead.

### FL-28 External APIs move fields [field]
- A provider's new API version relocated a field; the handler then ran
  `where(col, null)->update(...)` and flipped many unrelated rows to a failing
  billing state. **Do:** null/empty guard before any `update()`/`delete()` keyed by
  an external id; read with fallbacks; test the absent-field payload.

---

## E. Security-design lessons

### FL-15 SSRF sinks [field] — see `05`
### FL-16 Testing limits safely [field] — see `04`
### FL-17 Concurrency control groups [field] — see `08`

### FL-18 Fail closed; test forgotten characters [field]
- An empty webhook secret computes a valid HMAC with an empty key. A slug regex correct in
  one language matched a trailing newline in another (`$`). **Do:** explicit unset→reject
  branch and a test using the empty secret; allow-list tests with newline, NUL, unicode,
  over-length.

### FL-19 Blast radius of security settings [field]
- A global token-expiry setting would have invalidated every existing token at once; the
  per-token expiry applied only to new ones. Ask "existing records or only new ones?" and
  test with an old-style fixture.

### FL-20 Trust a header only when the writer cannot be impersonated [field] — see `07`

### FL-27 Earlier hardening constrains later features; state limits [field]
- A frame-denial header set earlier decided where an embeddable relay page could live; a
  widget's DOM being hidden defeated a selector-based test. State each control's residual
  risk in the report (an Origin check does not stop non-browser clients).

---

## F. Operations and hand-offs

### FL-21 Find every caller before closing a path [field]
- A cache-purge endpoint was to be blocked externally; the server itself called it through
  the public URL. **Do:** find callers first (including self-calls), move them to an
  internal address, then block. For paired client+server changes, make the safe half live
  first and put secrets in first; inventory callers of every endpoint you protect.

### FL-22 "Stopped" means no launch path remains [field]
- The app had several supervisors besides the named one (process manager, scheduler, service
  unit), and the deploy health check had been testing a different app than the one it was meant to.

### FL-23 A leaked secret is valid wherever it was typed [field]
- Searching where an old password was reused printed the matching line — which *was* the
  secret itself (a mistyped secret alone on a history line). The same string also worked in other
  credential stores.
- **Do:** report counts, file names, key names only; search where it was **stored** and
  where it **works**.

### FL-24 `sudo -n -l` cannot prove passwordless [field]
- It reports "allowed", including allowed-with-password. Run a harmless command with
  `sudo -n` to prove NOPASSWD.

### FL-25 Untracked, un-ignored secret backups [field]
- A backup of a production environment file sat in a repository working tree, not ignored,
  holding secrets identical to the live ones. Inventory by name and hash, get an explicit yes
  before deleting, and close the gap (ignore rules for env-file variants).

### FL-32 Hand-offs [field]
- A privileged command was handed to the user without saying which machine/account to run
  it on; the file "was not found" because it existed on the other host.
- **Do:** each hand-off states where it runs (host + account + how to get there), uses
  absolute paths, includes a one-line check that separates "wrong machine" from "file
  missing", and gives the rollback first.

### FL-33 Never carry a secret you do not need [field]
- Hand the user a one-line interactive command for steps that need a secret; verify
  read-only afterwards; prove a config rewrite is lossless (diff) before touching it; write
  the backlog down where the next session will find it.
