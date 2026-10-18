#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vic-41148
# SPDX-License-Identifier: MIT
"""Scan modem MBN/mcfg files for IMS-related configuration strings.

Why this exists: on Samsung SM7325 the answer to "is VoLTE configured
in the modem's carrier files?" turned out to be *no* -- no IMS NV items
in any of the 69 MBNs on the device, and no India-specific MBN at all.
IMS policy lived entirely on the Android side plus runtime QMI IMSS
provisioning. This script is the check that establishes that on your
own firmware, so you do not have to take it on trust.

This is a string-level scan. For structural extraction (item names,
types, values) use sbaresearch/mbn-mcfg-tools (`mbn-tool -e <mbn>`)
and diff the output; that is how the finding above was cross-checked.

Usage:
    tools/scan-mbn-ims.py /path/to/firmware          # walk and scan
    tools/scan-mbn-ims.py a.mbn b.mbn
    tools/scan-mbn-ims.py --diff a.mbn b.mbn         # compare two files
    tools/scan-mbn-ims.py --list-tokens

Read-only. Never bundles or writes firmware.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Tokens that would indicate modem-side IMS configuration.
TOKENS = [
    "ims",
    "imss",
    "mmtel",
    "volte",
    "vonr",
    "vowifi",
    "viwifi",
    "vilte",
    "pcscf",
    "smsoip",
    "sms_over_ims",
    "qmi_ims",
    "ims_enable",
    "imsenable",
    "registrationconfiguration",
    "sip_config",
    "sipconfig",
]

TOKEN_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in TOKENS) + r")\b", re.IGNORECASE
)
# Printable ASCII runs of 4+ characters, as they appear in the binary.
STR_RE = re.compile(rb"[\x20-\x7e]{4,}")


def strings(path: Path) -> list[str]:
    data = path.read_bytes()
    return [m.group().decode("latin-1") for m in STR_RE.finditer(data)]


def find_tokens(path: Path) -> list[str]:
    hits: list[str] = []
    for s in strings(path):
        if TOKEN_RE.search(s):
            hits.append(s.strip())
    # stable order, de-duplicated
    seen: dict[str, None] = {}
    for h in hits:
        seen.setdefault(h, None)
    return list(seen)


def collect_mbns(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_dir():
            out.extend(sorted(p.rglob("*.mbn")))
        elif p.is_file():
            out.append(p)
        else:
            print(f"skip (not found): {p}", file=sys.stderr)
    return out


def cmd_scan(paths: list[Path], show: int) -> int:
    files = collect_mbns(paths)
    if not files:
        print("no .mbn files found", file=sys.stderr)
        return 2

    with_hits = 0
    for f in files:
        hits = find_tokens(f)
        if hits:
            with_hits += 1
            print(f"\n{f}")
            for h in hits[:show]:
                print(f"    {h[:100]}")
            if len(hits) > show:
                print(f"    ... {len(hits) - show} more")

    print(
        f"\n{len(files)} MBN file(s) scanned, {with_hits} containing"
        f" IMS-related strings."
    )
    if with_hits == 0:
        print(
            "Result matches the SM7325 finding: no modem-side IMS policy."
            " Look Android-side instead (CarrierConfig, vendor IMS profiles,"
            " runtime QMI IMSS provisioning) -- see docs/carrier-config.md."
        )
    return 0


def cmd_diff(a: Path, b: Path, show: int) -> int:
    if not a.is_file() or not b.is_file():
        print("--diff needs two files", file=sys.stderr)
        return 2
    sa, sb = set(find_tokens(a)), set(find_tokens(b))
    only_a, only_b = sorted(sa - sb), sorted(sb - sa)
    print(f"A: {a}  ({len(sa)} IMS-ish strings)")
    print(f"B: {b}  ({len(sb)} IMS-ish strings)")
    print(f"\nonly in A ({len(only_a)}):")
    for s in only_a[:show]:
        print(f"    {s[:100]}")
    print(f"\nonly in B ({len(only_b)}):")
    for s in only_b[:show]:
        print(f"    {s[:100]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--diff", nargs=2, type=Path, metavar=("A", "B"))
    ap.add_argument("--show", type=int, default=10, help="strings per file (default 10)")
    ap.add_argument("--list-tokens", action="store_true")
    args = ap.parse_args()

    if args.list_tokens:
        print("\n".join(TOKENS))
        return 0
    if args.diff:
        return cmd_diff(args.diff[0], args.diff[1], args.show)
    if not args.paths:
        ap.print_help()
        return 1
    return cmd_scan(args.paths, args.show)


if __name__ == "__main__":
    raise SystemExit(main())
