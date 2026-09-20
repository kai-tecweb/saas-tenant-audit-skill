#!/usr/bin/env bash
# Pre-publication leak scanner for this repository (or any docs repo).
#
# Prints COUNTS and FILE NAMES only, never the matching text (lesson FL-23: matched
# lines can be the secret itself). Exit status 1 if anything is found.
#
# Usage:
#   scripts/leak_scan.sh [--terms private-terms.txt] [path]
#
#   --terms FILE   one case-insensitive fixed string per line: client/company names,
#                  domains, project code names, personal names ... (keep this file OUT
#                  of the repository).
#   path           directory to scan (default: the repository root, three levels above this
#                  script's directory).
#
# NOTE: the scan skips the .git directory. It cannot see the git author name/e-mail of
# your commits or old history: check `git log --format='%an <%ae>'` yourself before publishing.
# Matching is exact (case-insensitive) text: list spelling variants (romaji, katakana,
# abbreviations) of every name as separate terms.
#
# Built-in generic checks: private-key blocks, common API-key/token shapes, public
# IPv4 addresses (RFC 5737 documentation ranges and private/loopback ranges are allowed),
# e-mail addresses (reserved example domains and the allow-list are ignored),
# long random-looking assignment values on KEY/SECRET/TOKEN/PASSWORD lines.
set -u

TERMS=""
ROOT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --terms) TERMS="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) ROOT="$1"; shift ;;
  esac
done
if [ -z "$ROOT" ]; then
  ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
fi
[ -d "$ROOT" ] || { echo "not a directory: $ROOT"; exit 2; }

# Files to skip (binary, VCS). Allow-listed e-mail addresses go in .leak-allow-emails (one per line).
EXCL=(--exclude-dir=.git --exclude-dir=node_modules --binary-files=without-match)
ALLOW_EMAILS="$ROOT/.leak-allow-emails"
# "found" lives in a file: report() runs at the end of a pipeline (a subshell), so a plain
# variable set there would be lost and the script would wrongly exit 0.
FLAG="$(mktemp)"
trap 'rm -f "$FLAG"' EXIT

report() {  # label, file-list on stdin
  local label="$1" files count
  files="$(sort -u)"
  if [ -n "$files" ]; then
    count="$(printf '%s\n' "$files" | wc -l | tr -d ' ')"
    echo "FOUND [$label]: $count file(s)"
    printf '%s\n' "$files" | sed "s|^$ROOT/||; s|^|    |"
    echo 1 >> "$FLAG"
  else
    echo "ok    [$label]"
  fi
}

# 1. Private-key blocks
grep -rlE "${EXCL[@]}" -e '-----BEGIN [A-Z ]*PRIVATE KEY-----' "$ROOT" 2>/dev/null | report "private key block"

# 2. Common API-key / token shapes (prefix-based formats used by popular services)
grep -rlE "${EXCL[@]}" -e '(sk-[A-Za-z0-9_-]{20,}|sk_(live|test)_[A-Za-z0-9]{16,}|whsec_[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35})' "$ROOT" 2>/dev/null | report "token-shaped strings"

# 3. Long secret-looking assignments (KEY=..., secret: "...", etc.)
grep -rlEi "${EXCL[@]}" -e '(secret|token|password|passwd|api[_-]?key)[A-Za-z0-9_]*[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9+/_=-]{24,}' "$ROOT" 2>/dev/null | report "long secret-looking assignments"

# 4. Public IPv4 addresses (allow loopback, private, link-local, RFC 5737 documentation, 0.0.0.0, version-like)
files_ip="$(grep -rEl "${EXCL[@]}" -e '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' "$ROOT" 2>/dev/null | while read -r f; do
  if grep -Eoh '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' "$f" | grep -Ev '^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|169\.254\.|192\.0\.2\.|198\.51\.100\.|203\.0\.113\.|0\.0\.0\.0|255\.|100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.)' | awk -F. '$1<=255 && $2<=255 && $3<=255 && $4<=255' | grep -qv '^0\.'; then echo "$f"; fi
done)"
printf '%s\n' "$files_ip" | grep -v '^$' | report "public-looking IPv4 addresses"

# 5. E-mail addresses (ignore reserved example domains and the allow-list)
files_mail="$(grep -rEl "${EXCL[@]}" -e '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$ROOT" 2>/dev/null | while read -r f; do
  grep -Eoh '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$f" \
    | grep -Evi '@(example\.(com|org|net|invalid|test)|.*\.invalid|.*\.test|localhost)$' \
    | { if [ -f "$ALLOW_EMAILS" ]; then grep -vixFf "$ALLOW_EMAILS"; else cat; fi; } \
    | grep -q . && echo "$f"
done)"
printf '%s\n' "$files_mail" | grep -v '^$' | report "e-mail addresses (add intentional ones to .leak-allow-emails)"

# 6. Private terms (client names, domains, code names ...)
if [ -n "$TERMS" ]; then
  [ -f "$TERMS" ] || { echo "terms file not found: $TERMS"; exit 2; }
  n=0
  while IFS= read -r term; do
    [ -z "$term" ] && continue
    case "$term" in \#*) continue ;; esac
    n=$((n + 1))
    grep -rliF "${EXCL[@]}" -e "$term" "$ROOT" 2>/dev/null | report "private term #$n"
  done < <(tr -d '\r' < "$TERMS")
  echo "checked $n private term(s) (terms are not printed)"
else
  echo "note  no --terms file given: client/company/domain names were NOT checked"
fi

if [ -s "$FLAG" ]; then echo "RESULT: findings above (counts and file names only)"; exit 1; else echo "RESULT: clean"; exit 0; fi
