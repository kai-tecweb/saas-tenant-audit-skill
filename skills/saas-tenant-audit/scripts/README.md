# scripts/

All scripts are dependency-free (Python 3 standard library and Bash) and print no secret values.

| Script | Purpose |
|---|---|
| `tenant_probe.py` | Run a JSON plan of two-tenant black-box requests. One line per request with `expected=` next to `actual=` (a list of acceptable codes is allowed); asserts positive controls, "same as never-existed" equality (existence oracle: status, body shape, or a hash for non-JSON) and that the victim's data snapshot did not change (compared with the previous snapshot). Redirects are not followed. Bodies are not printed unless you pass `--preview N`. Exit 1 on any failure. |
| `selftest.sh` | Proves `tenant_probe.py` can fail: it must pass against a secure mock server and fail (existence oracle, cross-tenant write, redirect not followed, no body preview) against a deliberately vulnerable one. Run it after editing the probe. |
| `leak_scan.sh` | Pre-publication scan of a repository/docs for private-key blocks, token-shaped strings, public IPv4 addresses, e-mail addresses and your own private terms (`--terms file`, kept outside the repo). Prints counts and file names only. Skips `.git`. Exit 1 if anything is found. |

Limits of `tenant_probe.py` (use curl or your own code for these): multipart uploads,
raw/HMAC-signed bodies such as webhooks, parallel requests, capturing IDs from responses.
Plan files are code (`snapshot_cmd` runs in a shell) and may only reference tokens through
`ENV:NAME`; keep them out of shared places. See `references/08` for concurrency tests.

Both tools were tested against synthetic fixtures that are known to fail (a vulnerable mock
server; a directory with planted leaks) — a check that cannot fail is not a test (FL-08).

Contact: X (Twitter) https://x.com/iwasaki_dev40
