# saas-tenant-audit-skill

> **English** · [日本語](README.ja.md)

A [Claude Code](https://claude.com/claude-code) skill (SKILL.md format) for **black-box
security audits of multi-tenant SaaS products built with Laravel + Next.js**, written from
the point of view of *another tenant's account* — no source code or internal knowledge
required — and enriched with **failure patterns from a real audit-and-fix campaign**.

- Two skills, same content: **`saas-tenant-audit`** (English) and **`saas-tenant-audit-ja`** (日本語).
- MIT licensed. Contains **no client-specific information**: only abstracted procedures,
  checklists and lessons.
- Contact / feedback: **X (Twitter) — https://x.com/iwasaki_dev40**

## Why another security skill?

Most public security skills review code or map findings to standards. This one is built
around three things that were missing from the public skills we surveyed (see
[docs/comparison.md](docs/comparison.md)):

1. **Second-tenant black-box view.** You are Tenant A, an ordinary customer. You try to
   read, change or infer Tenant B's data through path IDs, JSON body fields, stored
   references, existence oracles, public widgets and anonymous endpoints — and you prove
   the victim's data did not change with before/after snapshots.
2. **Field-derived failure patterns.** 35 lessons (`FL-01 … FL-35`) from mistakes that were
   really made while auditing: cleanup steps piped through `grep` that hid a fatal error;
   assertions that accepted "some refusal" instead of the exact status; absence checks that
   passed because the request never reached the code; regression scripts that had silently
   gone stale; test traffic tripping the target's own rate limiter; and more.
3. **Laravel + Next.js multi-tenant focus** — Sanctum token expiry blast radius, mass
   assignment that silently drops the counted column, route handlers/Server Actions as
   public endpoints, ISR/sitemap cache invalidation, host-based custom domains — while the
   procedure itself stays stack-agnostic.

## What is inside

```
saas-tenant-audit-skill/
├── README.md / README.ja.md
├── LICENSE                     MIT
├── CHANGELOG.md  CONTRIBUTING.md
├── docs/
│   ├── comparison.md / comparison.ja.md   survey of existing public skills & standards
│   └── PUBLISHING.md                      maintainer checklist (bilingual)
└── skills/
    ├── saas-tenant-audit/      ← English skill
    │   ├── SKILL.md            entry point: method, rules, output
    │   ├── references/         00 scope & safety · 01 recon/inventory · 02 two-tenant matrix
    │   │                       03 lifecycle · 04 public abuse/cost · 05 SSRF · 06 authN/tokens/webhooks
    │   │                       07 perimeter & secrets · 08 concurrency/quotas
    │   │                       09 harness pitfalls (field lessons) · 10 reporting & severity
    │   │                       11 Laravel + Next.js notes · 12 multi-agent orchestration
    │   ├── templates/          audit-plan · authz-matrix · finding
    │   └── scripts/            tenant_probe.py · selftest.sh · leak_scan.sh · README
    └── saas-tenant-audit-ja/   ← Japanese skill (same layout)
```

## Install

Claude Code loads skills from `~/.claude/skills/` (personal) or `<project>/.claude/skills/`
(project).

```bash
git clone <this repository>
cp -r saas-tenant-audit-skill/skills/saas-tenant-audit    ~/.claude/skills/
cp -r saas-tenant-audit-skill/skills/saas-tenant-audit-ja ~/.claude/skills/   # optional, Japanese
```

Then ask, for example:

- "Audit this SaaS from another tenant's point of view; here is the staging URL and two
  test accounts." (the skill will first ask for scope and authorization)
- "Build the two-tenant authorization matrix for these routes."
- "Review my cleanup/verification script for the pitfalls in `09-harness-pitfalls`."
- "Write the finding report with OWASP/CWE mapping and a severity rank."

## Method (nine phases)

| # | Phase | Reference |
|---|---|---|
| 1 | Recon & entry-point inventory | `01-recon-and-inventory` |
| 2 | Two-tenant black-box matrix | `02-two-tenant-blackbox` |
| 3 | Lifecycle / soft-delete invariants | `03-lifecycle-invariants` |
| 4 | Public-endpoint abuse, AI/e-mail cost, rate limits, bot checks | `04-public-endpoint-abuse` |
| 5 | Outbound requests (SSRF) | `05-ssrf-and-outbound` |
| 6 | AuthN, tokens, password reset, webhooks | `06-authn-tokens-webhooks` |
| 7 | Perimeter, debug exposure, secrets | `07-perimeter-and-secrets` |
| 8 | Concurrency & quotas | `08-concurrency-and-quotas` |
| 9 | Report, fix, re-verify | `10-reporting-and-severity` |

Cross-cutting: `09-harness-pitfalls` (read before scripting), `12-orchestration`, `templates/`.

## The field lessons at a glance

Grouped; full text with symptom → why → do in `references/09-harness-pitfalls.md`.

- **Test design (A):** exact expected-vs-actual on one line (FL-06); assert preconditions
  (FL-07); positive control for absence checks (FL-08); stale regression scripts (FL-10);
  test the existing control before improving it (FL-11); use the real feature path (FL-30).
- **Test-data hygiene (B):** cleanup that cannot hide failure — raw output, prefix-based,
  baseline equality (FL-05); your traffic is subject to the target's defenses (FL-09);
  tooling that masquerades as product bugs (FL-12); kill by PID (FL-34).
- **Tooling & environment (C):** testing bot-protection widgets (FL-14); local runtime
  lacks an extension (FL-31); measure the limits you advertise (FL-35).
- **Authorization method (D):** three lenses (FL-01); IDs in JSON/stored fields (FL-02);
  existence oracles (FL-03); state at every entry point (FL-04); reachability vs priority
  (FL-29); status code ≠ correct content (FL-13); agents rate findings differently
  (FL-26); external APIs move fields (FL-28).
- **Security design (E):** SSRF sinks (FL-15); limits without side effects (FL-16);
  concurrency control groups (FL-17); fail closed & forgotten characters (FL-18); blast
  radius of settings (FL-19); trusting the right header (FL-20); limits of each control
  (FL-27).
- **Operations & hand-offs (F):** find every caller before closing a path (FL-21);
  "stopped" means no launch path (FL-22); leaked secrets (FL-23); `sudo -n -l` (FL-24);
  untracked secret backups (FL-25); hand-off commands (FL-32); never carry a secret you
  do not need (FL-33).

## Standards mapping

Findings are ranked by **exposure × impact** and mapped to OWASP Top 10 categories,
OWASP API Security Top 10 (2023) and one primary CWE — see
`references/10-reporting-and-severity.md`. Optional CVSS vector.

## Responsible use

For systems you **own or are explicitly authorized to test**. The skill starts with an
authorization gate, prefers scratch tenants and side-effect-free targets, forbids printing
secrets, and contains no exploit tooling. Do not use it against third-party services or
other customers' data.

## Scripts

- `tenant_probe.py` — runs a JSON plan of two-tenant requests, one `expected=`/`actual=`
  line per request, with positive controls, "same as never-existed" comparison, victim
  snapshot diff, no redirect following, and no body output by default.
- `selftest.sh` — proves the probe can fail (secure mock passes, vulnerable mock fails).
- `leak_scan.sh` — pre-publication scan for secrets, public IPs, e-mail addresses and your
  own private terms; prints counts and file names only.

Both were tested against synthetic fixtures that are *known to fail* (a deliberately
vulnerable mock server; a directory with planted leaks).

## Contributing, license, contact

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under the [MIT License](LICENSE).
Questions, corrections and new lessons: **X (Twitter) — https://x.com/iwasaki_dev40**
