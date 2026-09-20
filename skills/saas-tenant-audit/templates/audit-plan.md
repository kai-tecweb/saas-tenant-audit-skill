# Audit plan — <product> — <date>

## Authorization and scope
- Owner / approver: 
- Environment(s): local | staging | production (explicit yes from owner: y/n)
- Accounts I may create (scratch tenants): 
- Out of scope: 
- Contact if something unexpected happens: 
- Run prefix for all test data: `audit-<epoch>`

## Safety plan
- Fake addresses domain: `example.invalid`
- Vendor calls allowed (mail / LLM / payment / speech): none | listed: 
- Baseline snapshot method (tables/counters): 
- Cleanup method (prefix + tables): 
- Rate-limit plan (windows, reset method, what else lives in the reset store): 

## Phases (tick when done)
- [ ] 1 Recon & inventory  (`templates/authz-matrix.md` filled)
- [ ] 2 Two-tenant black-box matrix
- [ ] 3 Lifecycle invariants (state × entry point)
- [ ] 4 Public-endpoint abuse / cost
- [ ] 5 Outbound requests (SSRF)
- [ ] 6 AuthN / tokens / webhooks
- [ ] 7 Perimeter & secrets (only if in scope)
- [ ] 8 Concurrency & quotas
- [ ] 9 Report + cleanup proof

## Lenses used
- [ ] static read   - [ ] independent re-scan (different framing)   - [ ] live matrix

## Not tested (and why)
