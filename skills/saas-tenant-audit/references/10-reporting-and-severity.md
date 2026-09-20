# 10 — Reporting, severity and standards mapping

Contents: severity rubric · confirmation rule · standards mapping · finding format ·
what to report besides findings · fix and re-verification

## Severity rubric (two axes, then verify)

Score **Exposure** (who can trigger it) and **Impact** (what happens), then read the
cell. Adjust one level with a written reason (compensating control, unreachable feature).

| Exposure ↓ / Impact → | Low (nuisance, minor info) | Medium (limited data, small cost, single-tenant) | High (other tenants' data, money/cost at scale, account takeover) | Critical (mass data exposure, full takeover, RCE, secret disclosure enabling either) |
|---|---|---|---|---|
| Anonymous internet | Medium | High | Critical | Critical |
| Any logged-in tenant user | Low | Medium | High | Critical |
| Privileged/admin only | Low | Low | Medium | High |
| Requires local/host access | Low | Low | Medium | Medium |

Amplifiers: easy to automate; sequential/guessable IDs; no logging; affects every tenant;
irreversible. Reducers: feature unreachable in the product today (FL-29 — still list it),
strong compensating control verified live.

Optionally add a CVSS v3.1/v4.0 vector when the reader expects it. Keep the two-axis
rating as the primary, plain-language rank.

## Confirmation rule (FL-26)

Every finding needs **one minimal reproducing request** (or observation) recorded with
actual output. If severity is uncertain, one harmless confirming request settles it (for
example, debug mode: one request that triggers an error and shows exception class and
paths). Do not exploit further than needed. Do not average agent ratings; the
orchestrator confirms each candidate.

## Standards mapping (use names; check the current edition's numbering)

| Finding type | OWASP Top 10 (2021 id; category name is stable across editions) | OWASP API Top 10 (2023) | Typical CWE |
|---|---|---|---|
| Other tenant's object readable/writable by ID | A01 Broken Access Control | API1 BOLA | CWE-639, CWE-862, CWE-863, CWE-284 |
| Missing admin/role gate | A01 Broken Access Control | API5 BFLA | CWE-862, CWE-285 |
| Mass assignment / extra fields writable | A01 / A04 Insecure Design | API3 BOPLA | CWE-915 |
| Existence oracle (status/body differences) | A01 | API1 | CWE-204, CWE-203 |
| State ignored (deleted still public) | A01 / A04 | API1, API9 improper inventory | CWE-284, CWE-863 |
| No/weak rate limit on auth or public writes | A07 Auth Failures / A04 | API4 unrestricted resource consumption, API6 sensitive business flows | CWE-307, CWE-770, CWE-799 |
| Paid-API/e-mail abuse without cap | A04 | API4, API6 | CWE-770, CWE-400 |
| SSRF | A10 SSRF (folded into A01 in the 2025 edition) | API7 | CWE-918 |
| Weak password reset / enumeration / timing | A07 | API2 Broken Authentication | CWE-640, CWE-204, CWE-208 |
| Token never expires / not revoked | A07 | API2 | CWE-613 |
| Webhook signature not verified / fail-open | A08 Integrity Failures | API10 unsafe consumption | CWE-345, CWE-636 |
| Debug mode / verbose errors in production | A05 Misconfiguration | API8 | CWE-489, CWE-209 |
| Origin reachable around CDN, dev ports exposed | A05 | API8 | CWE-668, CWE-284 |
| Missing security headers | A05 | API8 | CWE-693 |
| Stored XSS via tenant content | A03 Injection | — | CWE-79 |
| Secrets in files/history/reuse | A02 Cryptographic Failures / A05 | — | CWE-798, CWE-522, CWE-312 |
| Race condition on quota/limit | A04 | API4, API6 | CWE-362, CWE-367 |
| Insecure default / fail-open config | A05 | API8 | CWE-1188, CWE-636 |

Use the mapping to help readers triage; do not pad findings with many IDs. One primary
CWE per finding.

## Finding format

Use `templates/finding.md`. Required fields: id, title, severity (exposure × impact),
affected entry point(s), summary, **reproduction with expected vs actual**, impact,
recommendation (concrete, with the residual risk it leaves), standards mapping, status
(open/fixed/verified), and evidence location. Keep secrets out of evidence.

## Report sections (beyond findings)

1. Scope, environment, authorization statement, dates.
2. Method summary (which phases ran, which lenses).
3. Inventory summary (counts by class: authenticated ID-taking, public writes, URL-taking,
   webhook, admin).
4. Matrix results (`expected | actual` table, pass/fail counts).
5. Findings ranked, grouped by root cause where several entry points share one.
6. **Not tested / out of scope**, and why (missing positive control, provider excluded,
   no production permission).
7. **Residual risks** of each control (FL-16, FL-27).
8. Cleanup proof: baseline before == after; artefacts removed.
9. Suggested backlog order: fix by exposure × impact, cheapest broad wins first
   (e.g. one guarded fetcher, one tenant-scoped finder used everywhere).

## Fix phase and re-verification

- Fix only what was asked; propose extras separately.
- Write the failing test first; keep the tenant-scoped finder as one helper used by all
  handlers so the convention (404) is enforced in one place.
- For concurrency/limits, run the broken version as a control (`08`).
- For paired client+server changes, roll out the half that is safe on its own first; put
  secrets in before the code that requires them; inventory every caller of what you protect
  (FL-21).
- Re-run the exact matrix rows that found the issue and the neighbouring rows, on the real
  environment, then do the cleanup proof.
- Add a regression test or a matrix row to the repository's test suite where the stack
  allows; keep the black-box matrix as a re-runnable script.
