#!/usr/bin/env bash
# Self-test for tenant_probe.py: it must PASS against a secure mock and FAIL (exit 1, with
# the specific reasons) against a deliberately vulnerable mock. A check that cannot fail is
# not a test (FL-08). Usage: scripts/selftest.sh
set -u
cd "$(dirname "$0")"
export PROBE_TOKEN_A=tokA PROBE_TOKEN_B=tokB
fail=0
run_case() {  # mode port
  local mode="$1" port="$2" out
  python3 selftest/mock_server.py "$mode" "$port" & local pid=$!
  sleep 0.7
  sed "s/PORT/$port/g" selftest/plan.template.json > "${TMPDIR:-/tmp}/probe-plan-$port.json"
  out="$(python3 tenant_probe.py "${TMPDIR:-/tmp}/probe-plan-$port.json" 2>&1)"; local code=$?
  kill "$pid"; wait "$pid" 2>/dev/null
  rm -f "${TMPDIR:-/tmp}/probe-plan-$port.json"
  printf '%s\n' "$out"
  echo "exit=$code"
  RESULT_CODE=$code; RESULT_OUT="$out"
}
echo "=== secure mock: expect exit 0 ==="
run_case secure 18191
[ "$RESULT_CODE" -eq 0 ] || { echo "SELFTEST FAIL: secure case should exit 0"; fail=1; }
echo; echo "=== vulnerable mock: expect exit 1 with oracle + data-changed reasons ==="
run_case vuln 18192
[ "$RESULT_CODE" -eq 1 ] || { echo "SELFTEST FAIL: vulnerable case should exit 1"; fail=1; }
printf '%s' "$RESULT_OUT" | grep -q "existence oracle" || { echo "SELFTEST FAIL: oracle not detected"; fail=1; }
printf '%s' "$RESULT_OUT" | grep -q "victim data CHANGED" || { echo "SELFTEST FAIL: cross-tenant write not detected"; fail=1; }
printf '%s' "$RESULT_OUT" | grep -q "body\[" && { echo "SELFTEST FAIL: body preview printed without --preview"; fail=1; }
[ "$fail" -eq 0 ] && echo "SELFTEST OK" || echo "SELFTEST FAILED"
exit "$fail"
