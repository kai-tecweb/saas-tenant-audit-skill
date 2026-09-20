# F-<nn>: <short title>

- **Severity:** <Critical|High|Medium|Low>  (Exposure: <anonymous|tenant user|admin|host> × Impact: <…>)
- **Status:** open | fixed | verified  (date)
- **Entry point(s):** METHOD /path (and siblings sharing the root cause)
- **Standards:** OWASP <Top 10 category>, API<n>, CWE-<one primary>

## Summary
One or two sentences: what is wrong and who can do what.

## Reproduction (minimal, with expected vs actual)
Preconditions: scratch tenants A and B, fixture ids …
1. `<request>`
   expected: `404`   actual: `200`
2. Evidence of impact: `<what changed / what was returned>`  (no secret values)

## Impact
What an attacker gains; how many tenants; automation potential.

## Recommendation
Concrete change. Then: **Residual risk after the fix:** …

## Verification (after fix)
Re-run rows: … Result: … Baseline before == after: yes/no
