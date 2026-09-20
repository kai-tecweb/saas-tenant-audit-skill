# Survey of existing public skills and standards

> **English** · [日本語](comparison.ja.md)

Surveyed on 2026-09-20 from public repository descriptions and documentation. It is **not
exhaustive**, most repositories were skimmed for structure rather than read in full, and
details (licenses, sizes, features) may have changed — check each source. Listing a project
here is not a criticism; the point is to show where this skill fits.

## Public skills / agent prompts we looked at

| Project | What it is | Mode | Notes relevant to this skill |
|---|---|---|---|
| [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) (MIT) | `/security-review` command and GitHub Action | Diff-based code review | Confidence gate and a long false-positive exclusion list; does not run the app |
| [trailofbits/skills](https://github.com/trailofbits/skills) (CC-BY-SA-4.0) | Marketplace of many plugins (static analysis, variant analysis, insecure defaults …) | Code review + tooling | We did not see a multi-tenant web-app authorization skill |
| [agamm/claude-code-owasp](https://github.com/agamm/claude-code-owasp) (MIT) | OWASP knowledge base skill with per-language references | Code review | Good progressive disclosure; a knowledge base, not a test procedure |
| [afiqiqmal/claude-security-audit](https://github.com/afiqiqmal/claude-security-audit) | Large checklist tool; detects Laravel/Next.js; has a SaaS multi-tenant pack and a "gray-box" mode | Mostly checklist/code | Closest in scope; license not verified. We did not see a two-tenant black-box procedure or lessons-learned material in its description |
| [AgriciDaniel/claude-cybersecurity](https://github.com/AgriciDaniel/claude-cybersecurity) (MIT) | Large multi-agent code-review skill with a scoring rubric | Code review | Laravel/Next.js not explicitly listed |
| [netresearch/security-audit-skill](https://github.com/netresearch/security-audit-skill) | Script-driven PHP-oriented audit (CWE, CVSS) | Code + scripts | PHP/TYPO3 focus |
| [sickn33 laravel-security-audit](https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/laravel-security-audit/SKILL.md) | Single-file Laravel checklist (IDOR, mass assignment, policies) | White-box | No runtime verification, no Next.js |
| [VicKayro/claude-security-audit](https://github.com/VicKayro/claude-security-audit) (MIT) | Single command file (French) | Code review | Asks for the environment first |
| [McGo/claude-code-security-audit](https://github.com/McGo/claude-code-security-audit) (MIT) | Skill with numeric score and an output-language switch (`lang=de`) | Code review | We did not see IDOR/multi-tenant coverage in its description |
| [toshipon/claude-code-security-audit-skill](https://zenn.dev/toshipon/articles/claude-code-security-audit-skill) | Japanese skill, 24 references, 8 phases; Next.js/Supabase | Static + browser | "Evidence-first" rule and "reject false rationalisations" section; targets Supabase, not Laravel |
| [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) (Apache-2.0) | Hundreds of security skills incl. API BOLA/IDOR testing | Various | Multi-account testing; no cleanup/two-tenant hygiene guidance seen |
| [Orizon-eu/claude-code-pentest](https://github.com/Orizon-eu/claude-code-pentest) (MIT) | Black-box pentest skills/scripts, CVSS recalculation | Black-box | Generic, not tenant-focused |

## Standards and checklists this skill leans on

- OWASP Top 10 (2021; a 2025 edition exists and renumbers some categories — the skill maps
  by category *name*), OWASP API Security Top 10 (2023), CWE, optional CVSS.
- OWASP Authorization Regression Testing Cheat Sheet (actor/resource/action matrix, be
  consistent about 403 vs 404) and OWASP Multi-Tenant Security Cheat Sheet (tenant from the
  identity, tenant in cache/rate-limit keys, tenant context in queue consumers).
- OWASP Laravel Cheat Sheet; Next.js security guidance (Data Access Layer, Server Actions as
  public endpoints); the widely published Next.js middleware-bypass advisory.
- Claude Code skill authoring guidance: minimal frontmatter, short `SKILL.md`,
  one-level-deep `references/`, contents lists on long files, scripts for deterministic steps.

## Where this skill differs

1. **Second-tenant black-box procedure** with before/after victim snapshots, denial
   conventions, existence-oracle comparison and IDs hidden in data — rather than a code
   checklist.
2. **Field lessons (FL-01 … FL-35)** about the audit *process and test harness*, which we did
   not find covered elsewhere.
3. **Laravel + Next.js multi-tenant SaaS** specifics in one place.
4. **Bilingual (English/Japanese)** from one method, kept in sync.

Anything here that is out of date or wrong: please tell us — X (Twitter)
https://x.com/iwasaki_dev40
