---
name: saas-tenant-audit
description: Black-box security audit of a multi-tenant SaaS (Laravel API + Next.js frontend) from the point of view of another tenant's account, with no internal knowledge. Covers cross-tenant authorization (IDOR/BOLA), lifecycle/soft-delete invariants, public-endpoint abuse and AI/email cost, SSRF, auth tokens and webhooks, perimeter and secrets, concurrency and quotas, plus a catalogue of test-harness pitfalls learned from real audits. Use when asked to audit, pentest, harden or "review the security" of your own or an authorized SaaS, to design a two-tenant test matrix, to write or verify a security fix, or to report findings with OWASP/CWE mapping.
license: MIT
---

# SaaS tenant-isolation & abuse audit (black-box, Laravel + Next.js)

Contact / feedback: X (Twitter) https://x.com/iwasaki_dev40

This skill turns one real end-to-end audit-and-fix campaign (verified in production) into a repeatable procedure. Its three
differentiators:

1. **Black-box, second-tenant point of view.** You act as an ordinary logged-in user of
   *another* tenant ("Tenant A") and try to reach, change, or infer the data of "Tenant B",
   using only what any customer can see: the web app, its JavaScript bundle, its public
   pages, and its API responses. Code reading is a second lens, never the only one.
2. **Field-derived failure patterns.** `references/09-harness-pitfalls.md` lists mistakes
   that were actually made while auditing (green tests that could not fail, cleanup that hid
   fatal errors, assertions that accepted "some refusal" instead of the exact status, ...).
   Read it before you write any verification script.
3. **Laravel + Next.js multi-tenant SaaS focus.** Stack notes are in
   `references/11-stack-laravel-nextjs.md`; everything else is stated generically so it
   transfers to other stacks.

## 0. Authorization gate (do this first, every time)

Only audit systems the user owns or has written permission to test. Ask for (or confirm
from the conversation): the target environment(s), whether production may be touched,
which accounts are yours to create, and what is out of scope. If any of that is unclear,
stop and ask. Do not test third-party services the target depends on (payment provider,
CAPTCHA vendor, AI vendor) beyond calling them the way the product itself does. Details:
`references/00-scope-and-safety.md`.

## Method at a glance

| Phase | Question it answers | Reference |
|---|---|---|
| 1. Recon & inventory | What entry points exist, and what does each one do to whom? | `01-recon-and-inventory.md` |
| 2. Two-tenant black-box matrix | Can Tenant A read/change/infer Tenant B's data through any ID, field or side channel? | `02-two-tenant-blackbox.md` |
| 3. Lifecycle invariants | Does every entry point respect deleted / unpublished / expired state? | `03-lifecycle-invariants.md` |
| 4. Public-endpoint abuse | Can an anonymous or free user burn money, send mail, or fill storage? | `04-public-endpoint-abuse.md` |
| 5. Outbound requests (SSRF) | Can the server be made to fetch something it should not? | `05-ssrf-and-outbound.md` |
| 6. AuthN, tokens, webhooks | Can accounts be taken over, enumerated, or state forged? | `06-authn-tokens-webhooks.md` |
| 7. Perimeter & secrets | Is the origin reachable around the CDN, is debug on, are secrets reused or stored? | `07-perimeter-and-secrets.md` |
| 8. Concurrency & quotas | Do "at most N" limits hold under parallel requests? | `08-concurrency-and-quotas.md` |
| 9. Report, fix, re-verify | How do we rank, fix, roll out and prove it? | `10-reporting-and-severity.md` |

Cross-cutting: `09-harness-pitfalls.md` (read before scripting), `12-orchestration.md`
(if you use sub-agents), `templates/` (plan, matrix, finding), `scripts/` (probe skeleton,
publication leak scanner).

## Operating rules (non-negotiable)

These are the rules that the field lessons converged on. Each links to the lesson id
(`FL-nn`) in `references/09-harness-pitfalls.md`.

1. **Investigate before you change.** Audit phases are read-only or use your own scratch
   tenants. Do not modify the target's code or data until the user asks for the fix
   phase. Keep "found" and "fixed" in separate steps.
2. **Baseline, then compare.** Snapshot row counts (or an equivalent) before any
   scenario and diff after cleanup. Any difference is leftover test data. (FL-05, FL-09)
3. **Assert the exact expected status next to the actual one**, on the same output line.
   "Refused" is not a result; `404 expected / 404 actual` is. (FL-06)
4. **Print and assert the precondition** of every before/after test, and give every
   absence check a positive control. (FL-07, FL-08)
5. **Never filter the output of setup or cleanup steps.** No `| grep`, no `2>/dev/null`
   on steps whose failure matters. End cleanup with a baseline-equality check.
   (FL-05)
6. **Your test traffic is subject to the target's defenses.** Rate limits, sessions in a
   shared cache, and CDN bot rules will hit your own harness. Plan for it. (FL-09, FL-12)
7. **Use side-effect-free targets when exercising limits** (non-existent IDs, fake
   addresses on reserved domains), so no mail, payment, or AI call is triggered.
   (FL-16)
8. **A failing check is a question, not a verdict.** Compare with a control ("same as a
   resource that never existed") before deciding whether the product or the test is
   wrong. (FL-04, FL-06)
9. **State what each control cannot prevent.** Every recommendation ends with its
   residual risk. (FL-16, FL-27)
10. **Never print secrets.** Report counts, file names and key *names*; never matched
    lines or values. New secrets travel via stdin or mode-600 files. (FL-23, FL-33)

## Output

Deliver, in this order: (1) scope and environment statement; (2) the endpoint inventory
with the tenant-scope/state/cost columns filled; (3) the executed test matrix with
`expected | actual` per row; (4) findings using `templates/finding.md`, ranked using
`references/10-reporting-and-severity.md` with OWASP/CWE mapping; (5) the list of things
that were *not* tested and why; (6) cleanup proof (baseline before = after). Report in
the chat unless the user asks for a file; do not leave scripts or logs in the target
repository.

## When you also fix

Switch explicitly to the fix phase only when asked. For each fix: write the test that
fails first, run the broken version as a control where concurrency or limits are
involved (FL-17), roll out server-side and client-side halves in the order that leaves no
window (FL-21), and re-run the exact matrix rows that found the issue.

## License and contact

MIT (see repository `LICENSE`). Questions, corrections and additional field lessons are
welcome via X (Twitter): https://x.com/iwasaki_dev40
