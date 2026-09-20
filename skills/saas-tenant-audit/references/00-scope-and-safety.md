# 00 — Scope, authorization and safe operation

## Authorization checklist (answer before sending a single probe)

- [ ] I own the target, or the owner has authorized this test (ideally in writing).
- [ ] The environment is named: local / staging / production. If production, the owner
      has said so explicitly.
- [ ] I may create my own accounts and tenants ("scratch tenants") and delete them after.
- [ ] Out of scope is written down (third-party providers, other tenants' real data,
      denial-of-service style load, social engineering, physical access).
- [ ] A person is reachable if something unexpected happens (mail sent to a real
      customer, data changed, service slow).

If any box is unchecked, ask. Do not infer authorization from the fact that the target is
reachable.

## Production testing rules

Production is often the only environment that has the real proxy chain, CDN, queue
workers and data volume, so testing there is sometimes necessary. Make it safe:

1. **Scratch tenants only.** Create two fresh tenants (A = attacker, B = victim) with
   fake, clearly-labelled data and a unique run prefix (for example `audit-<epoch>`).
   Never use a real customer as the victim.
2. **Fake addresses on reserved domains** (`example.invalid`, `example.test`) for every
   e-mail, so nothing reaches a real inbox. If you must prove real mail delivery, use one
   mailbox you own.
3. **Side-effect-free targets for limit tests.** Trip rate limiters through routes that
   fail *after* the limiter counts but *before* any side effect (a non-existent ID gives
   404 with no mail/AI/payment call). (FL-16)
4. **No load tests.** Concurrency tests use tens of requests, not thousands, and only
   against your own scratch tenant. (FL-17)
5. **Snapshot before, diff after.** Row counts per table you touch, plus cache/queue/log
   artefacts. Cleanup ends with "before == after". (FL-05)
6. **Cost awareness.** Anything that calls a paid API (LLM, image generation,
   speech-to-text, SMS) needs an explicit go-ahead; prefer paths that reject before the
   vendor call.
7. **One harmless confirmation request per uncertain severity.** Do not exploit further
   than needed to classify (see `10-reporting-and-severity.md`).

## What never to do

- Do not print, store or transmit secrets you come across. Note their *existence* and
  location class (file name, key name, count) and stop. (FL-23, FL-33)
- Do not test other customers' live data, or a third party's systems, even "just to see".
- Do not use offensive techniques against production that could degrade it (mass
  enumeration, large payloads, slow-loris, brute force of real accounts).
- Do not leave test users, tokens, files, cache keys or queue rows behind.
- Do not run privileged (root/sudo) changes without a reviewed one-step script, the
  rollback stated first, and a way to verify afterwards without privileges. (FL-32)

## Access level

Some steps (database snapshots, clearing caches or rate-limit counters, reading server logs) need access to the scratch environment beyond an ordinary customer account. State which level you have: **customer-level** (API and web only) or **environment-level**. With customer-level access, take snapshots through the API (read the victim tenant's own list/detail endpoints *as the victim*), clean up with the product's own delete endpoints and fresh identifiers, and list what could not be verified.

## Environment fidelity notes

- Local runs often lack the extensions/services the real environment has (HTTP client
  extension, image library, the real proxy). Say what could not be tested locally and
  test it on the real host with a scratch harness. (FL-31)
- Your own tooling can be blocked by the CDN (default HTTP-client User-Agent → 403).
  Use a browser-like UA for probes and note it. (FL-12)
