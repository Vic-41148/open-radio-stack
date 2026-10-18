#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Vic-41148
# SPDX-License-Identifier: MIT
# Symbol inventory of a Samsung RIL binary, for pre-flight addressing.
#
# Give it a RIL you extracted yourself. This script never downloads,
# ships or accepts a vendor binary into this repo: you point it at your
# own copy, it prints symbols, and that is all.
#
# Usage:
#   tools/dump-ril-symbols.sh ~/extract/vendor/lib64/libsec-ril.so
#   tools/dump-ril-symbols.sh ~/extract/.../libsec-ril.so --filter data
#
# Needs binutils (nm). For the RIL, check both libsec-ril.so and any
# libsec-ril-*.so variants. Implementations differ per base.
set -uo pipefail

if [ $# -lt 1 ]; then
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
fi

RIL=$1
FILTER=${3:-}
shift || true

[ -f "$RIL" ] || { echo "no such file: $RIL" >&2; exit 1; }
command -v nm >/dev/null 2>&1 || { echo "binutils (nm) not found" >&2; exit 1; }

echo "# binary: $(basename "$RIL")"
echo "# size:   $(stat -c '%s' "$RIL") bytes"
echo "# sha256: $(sha256sum "$RIL" | awk '{print $1}')"
echo "# (record the hash: your analysis is only valid for this exact build)"
echo

# Dynamic symbols, demangled. -C for C++ classes/methods, -D for dynsym.
if [ -n "$FILTER" ]; then
  nm -D -C --defined-only "$RIL" 2>/dev/null | grep -iE "$FILTER"
else
  nm -D -C --defined-only "$RIL" 2>/dev/null
fi

echo
echo "# add the offset discipline from tools/rea-address-cheatsheet.md before"
echo "# trusting any address you read here."
