#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
mkdir -p "$TMPDIR/home" "$TMPDIR/bin"
calls="$TMPDIR/calls"

cat >"$TMPDIR/bin/nixos-shell" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$NIXOS_TEST_CALLS"
printf 'ok\n'
SH
chmod +x "$TMPDIR/bin/nixos-shell"

run_enable() {
  HOME="$TMPDIR/home" \
    NIXOS_PATH="$ROOT" \
    NIXOS_TEST_CALLS="$calls" \
    PATH="$TMPDIR/bin:$ROOT/bin:$PATH" \
    nixos-plugin-enable "$@"
}

run_enable nixos.active-window --section right >/dev/null
grep -Fqx 'shell enablePlugin nixos.active-window {"section":"right"}' "$calls" ||
  fail "plugin enable did not combine activation and placement"
pass "plugin enable combines activation and placement in one shell mutation"

run_enable nixos.clock --before nixos.weather >/dev/null
grep -Fqx 'shell enablePlugin nixos.clock {"before":"nixos.weather"}' "$calls" ||
  fail "plugin enable did not preserve relative placement"
pass "plugin enable forwards relative placement"

run_enable nixos.dropbox >/dev/null
grep -Fqx 'shell enablePlugin nixos.dropbox {}' "$calls" ||
  fail "plugin enable did not use manifest-default placement"
pass "plugin enable leaves default placement to the registry"

if run_enable nixos.bar --section right >/dev/null 2>&1; then
  fail "plugin enable accepted placement for a full bar"
fi
pass "plugin enable rejects placement for full bars"
