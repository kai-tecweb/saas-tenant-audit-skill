#!/usr/bin/env python3
"""Two-tenant black-box probe runner (dependency-free skeleton).

Reads a JSON plan and runs each request as the named actor, printing one line per
request with `expected=` and `actual=` side by side (lesson FL-06). Exits non-zero if
any row does not match, if a positive control fails, or if the victim's data snapshot
changed.

Usage:
    python3 tenant_probe.py plan.json [--base-url URL] [--user-agent UA] [--preview N]

Plan format (JSON, no comments):
{
  "base_url": "https://staging.example.test/api/v1",
  "actors": {
    "A":    {"token": "ENV:TOKEN_A"},
    "B":    {"token": "ENV:TOKEN_B", "scheme": "Token"},
    "anon": {}
  },
  "vars": {"A1": "101", "B1": "202", "X": "999999999"},
  "snapshot_cmd": "python3 dump_victim.py",
  "rows": [
    {"id": "own",     "actor": "A",    "method": "GET",   "path": "/things/{A1}", "expected": 200, "control": true},
    {"id": "foreign", "actor": "A",    "method": "GET",   "path": "/things/{B1}", "expected": [404]},
    {"id": "never",   "actor": "A",    "method": "GET",   "path": "/things/{X}",  "expected": 404, "same_as": "foreign"},
    {"id": "anon",    "actor": "anon", "method": "GET",   "path": "/things/{B1}", "expected": [401, 403]},
    {"id": "write",   "actor": "A",    "method": "PATCH", "path": "/things/{B1}", "body": {"name": "x"}, "expected": 404}
  ]
}

Actor keys: "token" (must be 'ENV:NAME' - literal secrets are refused), "scheme"
(default "Bearer"; use "Token" etc.), "header" (send the token in this header instead of
Authorization, scheme ignored), "base_url" (per-actor base, e.g. a tenant sub-domain),
"headers" (extra fixed headers). Row keys: "headers" (extra per-request headers such as
Host, Origin, Idempotency-Key), "expected" (an int or a list of acceptable ints),
"control" (must pass; otherwise later rows are reported UNPROVEN), "same_as" (status and
body shape - or a body hash for non-JSON - must equal another row: existence-oracle
check), "snapshot" (force the victim-snapshot check; it is automatic for
POST/PUT/PATCH/DELETE rows when snapshot_cmd is set).

Rules baked in (see references/09-harness-pitfalls.md):
  * expected and actual are printed on the same line; the exact status is asserted.
  * the snapshot is compared with the PREVIOUS snapshot, so one change does not make every
    later row fail; a change after a GET row is also reported (unattributed change).
  * redirects are NOT followed (a 3xx is reported as-is; a followed redirect can turn a POST
    into a GET or forward credentials).
  * bodies are not printed by default: only the status and the top-level key NAMES of a JSON
    response. Use --preview N to print the first N characters (may reveal secrets or personal
    data; use only on scratch tenants).
  * a failing snapshot command prints only its exit code, never its output.

Limitations (use curl or your own code for these, see references/08): multipart uploads,
raw/HMAC-signed bodies (webhooks), parallel requests, capturing IDs from responses. Plan
files are code (snapshot_cmd runs in a shell): keep them token-free and out of shared
places.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) tenant-probe"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def shape(value):
    """Reduce a JSON value to its structure (keys and types) for comparisons."""
    if isinstance(value, dict):
        return {k: shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return ["list", len(value) > 0] + ([shape(value[0])] if value else [])
    return type(value).__name__


def env_secret(value):
    if not isinstance(value, str) or not value.startswith("ENV:"):
        sys.exit("actor tokens must be given as 'ENV:NAME' (literal secrets in a plan file are refused)")
    name = value[4:]
    got = os.environ.get(name)
    if got is None:
        sys.exit(f"environment variable {name} is not set")
    return got


def subst(item, variables):
    if isinstance(item, str):
        for k, v in variables.items():
            item = item.replace("{" + k + "}", str(v))
        return item
    if isinstance(item, dict):
        return {k: subst(v, variables) for k, v in item.items()}
    if isinstance(item, list):
        return [subst(v, variables) for v in item]
    return item


def request(default_base, row, actors, variables, ua):
    actor = actors.get(row["actor"], {})
    headers = {"User-Agent": ua, "Accept": "application/json"}
    headers.update(actor.get("headers", {}))
    if actor.get("token"):
        token = env_secret(actor["token"])
        if actor.get("header"):
            headers[actor["header"]] = token
        else:
            headers["Authorization"] = f'{actor.get("scheme", "Bearer")} {token}'
    headers.update(subst(row.get("headers", {}), variables))
    body = row.get("body")
    data = None
    if body is not None:
        data = json.dumps(subst(body, variables)).encode()
        headers.setdefault("Content-Type", "application/json")
    base = actor.get("base_url", default_base)
    url = base.rstrip("/") + subst(row["path"], variables)
    req = urllib.request.Request(url, data=data, headers=headers, method=row.get("method", "GET"))
    try:
        with OPENER.open(req, timeout=30) as resp:
            status, text = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:  # includes 3xx because redirects are not followed
        status, text = exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:  # network error: report it, do not hide it
        return 0, None, "", f"network error: {type(exc).__name__}"
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    return status, parsed, text, ""


def signature(status, parsed, text):
    if parsed is not None:
        return (status, "json", json.dumps(shape(parsed), sort_keys=True))
    return (status, "text", hashlib.sha256(text.encode()).hexdigest()[:16])


def run_snapshot(cmd):
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if out.returncode != 0:
        print(f"snapshot command failed (exit {out.returncode}); its output is not shown")
        sys.exit(2)
    return out.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--base-url")
    ap.add_argument("--user-agent", default=DEFAULT_UA)
    ap.add_argument("--preview", type=int, default=0, help="print the first N characters of each body (may reveal secrets)")
    args = ap.parse_args()

    plan = json.load(open(args.plan))
    base = args.base_url or plan["base_url"]
    actors, variables, rows = plan.get("actors", {}), plan.get("vars", {}), plan["rows"]
    snap_cmd = plan.get("snapshot_cmd")
    previous = run_snapshot(snap_cmd) if snap_cmd else None
    if previous is not None:
        print(f"snapshot baseline captured ({len(previous)} bytes)")

    results, failures, control_ok = {}, 0, True
    for row in rows:
        status, parsed, text, err = request(base, row, actors, variables, args.user_agent)
        sig = signature(status, parsed, text)
        results[row["id"]] = sig
        expected = row["expected"]
        allowed = expected if isinstance(expected, list) else [expected]
        verdict, note = ("PASS" if status in allowed else "FAIL"), err
        if row.get("same_as"):
            ref = results.get(row["same_as"])
            if ref is None:
                verdict, note = "FAIL", f"same_as row '{row['same_as']}' has not run yet"
            elif ref != sig:
                verdict, note = "FAIL", f"differs from '{row['same_as']}' (status/shape/hash): existence oracle"
        if snap_cmd and (row.get("snapshot") or row.get("method", "GET").upper() in ("POST", "PUT", "PATCH", "DELETE")):
            current = run_snapshot(snap_cmd)
            if current != previous:
                verdict, note = "FAIL", (note + " victim data CHANGED").strip()
            previous = current
        if row.get("control"):
            if verdict != "PASS":
                control_ok = False
        elif not control_ok:
            verdict, note = "UNPROVEN", "a positive control failed earlier; result not trusted"
        if verdict in ("FAIL", "UNPROVEN"):
            failures += 1
        keys = sorted(parsed.keys())[:6] if isinstance(parsed, dict) else ("text" if parsed is None else "list")
        line = (f"{row['id']:<14} {row['actor']:<5} {row.get('method', 'GET'):<6} {row['path']:<32} "
                f"expected={'|'.join(map(str, allowed))} actual={status} {verdict} {note} | keys={keys}")
        if args.preview:
            line += f" | body[:{args.preview}]={text[:args.preview]!r}"
        print(line)

    if snap_cmd:
        final = run_snapshot(snap_cmd)
        if final != previous:
            print("FINAL: victim snapshot changed after the last checked row (unattributed change)")
            failures += 1
    print(f"\n{len(rows) - min(failures, len(rows))}/{len(rows)} rows passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
