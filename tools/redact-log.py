#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vic-41148
# SPDX-License-Identifier: MIT
"""Strip subscriber and dialog identifiers out of a radio/SIP log.

This repo's rule is "no unredacted traces", and this is the tool that
makes that rule cheap to keep. It is deliberately conservative: it
would rather over-redact than leak, and it always tells you what it
changed.

    tools/redact-log.py capture.log > capture.redacted.log
    tools/redact-log.py capture.log -o out.log --show-changes 2
    tools/redact-log.py capture.log --check        # exit 1 if it found anything
    tools/redact-log.py --list-rules

Pass 1 removes: IMSI/IMEI/ICCID-length digit runs, phone numbers, IPv4
and IPv6 addresses, MAC addresses, e-mail addresses, the user part of
SIP URIs, and SIP dialog material (Call-ID, tags, branches, digest
responses/nonces, SPI values, message ids).

What it cannot do: decide for you. Read the diff, and check anything
you add to the rule set against a real capture. Timestamps, counters,
ports and short numeric fields are left alone on purpose -- if your log
carries cell IDs or other quasi-identifiers, redact those by hand.

Addresses are validated with Python's ipaddress module, so a clock time
is never mistaken for an IPv6 address, and addresses written with "::"
are handled. Re-running it on already-redacted output changes nothing.

No network access, no writes except the file you name.
"""

from __future__ import annotations

import argparse
import ipaddress
import re
import sys
from pathlib import Path

KEEP_V6_PREFIX = 0

# ------------------------------------------------------------ helpers

EPOCH_MS_RE = re.compile(r"1\d{12}")                          # epoch milliseconds
STAMP_RE = re.compile(r"20\d{2}[01]\d[0-3]\d\d{2}\d{2}\d{2}")  # yyyymmddHHMMSS
MARKER_RE = re.compile(r"^<.*>$")                              # our own markers


def digits_repl(m: re.Match) -> str:
    """Classify a bare digit run instead of blindly redacting it."""
    s = m.group(0)
    body = s.lstrip("+")
    if EPOCH_MS_RE.fullmatch(body) or STAMP_RE.fullmatch(body):
        return s                       # a timestamp, not an identifier
    if not s.startswith("+") and len(body) < 10:
        return s                       # short counters, ports, codes
    if len(body) >= 14:
        return "<id>"                  # IMSI / IMEI / ICCID length
    return "<number>"                  # phone number


def _v6_keep(addr: str) -> str:
    if KEEP_V6_PREFIX <= 0:
        return "<ipv6>"
    hextets = addr.split(":")
    kept = ":".join(hextets[:KEEP_V6_PREFIX])
    return f"{kept}::<redacted>"


def ipv6_repl(m: re.Match) -> str:
    s = m.group(0)
    host, sep, plen = s.partition("/")
    host = host.strip("[]")
    try:
        addr = str(ipaddress.IPv6Address(host))
    except ValueError:
        return s                       # a clock time, or not an address
    if addr == "::1":
        return s
    out = _v6_keep(addr)
    if sep:
        out += f"/{plen}"
    return f"[{out}]" if s.startswith("[") else out


def ipv4_repl(m: re.Match) -> str:
    s = m.group(0)
    try:
        addr = ipaddress.IPv4Address(s)
    except ValueError:
        return s
    if addr.is_loopback:
        return s
    return "<ipv4>"


RULES: list[tuple[str, re.Pattern, object]] = [
    # ---- addresses -------------------------------------------------
    ("mac", re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b"), "<mac>"),
    ("ipv6", re.compile(
        r"\[?[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?:/\d{1,3})?\]?"
    ), ipv6_repl),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), ipv4_repl),
    # ---- long identifiers / numbers --------------------------------
    ("digits", re.compile(r"(?<![\w.+])\+?\d{6,22}(?![\w.])"), digits_repl),
    # ---- names / URIs ---------------------------------------------
    ("email", re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"), "<email>"),
    ("sip-user", re.compile(
        r"(?i)\b(sips?):(?!<)([^@\s;>,\"]+)@([A-Za-z0-9.\-:\[\]]+)"
    ), r"\1:<redacted>@\3"),
    ("tel", re.compile(r"(?i)\btel:(?!<)[+\d\-() ]+"), "tel:<redacted>"),
    # ---- SIP dialog material ---------------------------------------
    ("call-id", re.compile(r"(?i)\b(call-id)\s*:\s*(?!<)\S+"), r"\1: <redacted>"),
    ("tag", re.compile(r"(?i)(?<=[;?&])tag=(?!<)[^;\s>,]+"), "tag=<redacted>"),
    ("branch", re.compile(r"(?i)(?<=;)branch=(?!<)[^\s;>,]+"), "branch=<redacted>"),
    ("auth", re.compile(r"(?im)^(\s*)(Authorization\s*:)(?!\s*<).*$"),
     r"\1\2 <redacted>"),
    ("digest", re.compile(
        r'(?i)\b(response|nonce|opaque|cnonce)=(?!<)("[^"]*"|[^,\s]+)'
    ), r"\1=<redacted>"),
    ("spi", re.compile(r"(?i)\bspi-([cs])=(?!<)[0-9A-Fa-f]+"), r"spi-\1=<redacted>"),
    ("msg-id", re.compile(r"(?i)\bx-message-id\s*:\s*(?!<)-?\d+"),
     "x-message-id:<redacted>"),
    ("impi", re.compile(r"(?i)\bimpi\s*[=:]\s*(?!<)\S+"), "impi=<redacted>"),
]


def redact_line(line: str, counts: dict[str, int], samples: dict[str, str]) -> str:
    for name, rx, repl in RULES:
        source_line = line

        def apply(m: re.Match, repl=repl, name=name, source_line=source_line) -> str:
            old = m.group(0)
            new = repl(m) if callable(repl) else m.expand(repl)
            # Only count a real change: a rule that matches a timestamp or
            # an already-redacted marker leaves the text alone by design,
            # and must not make --check cry wolf.
            if new != old:
                counts[name] = counts.get(name, 0) + 1
                samples.setdefault(name, source_line.rstrip()[:160])
            return new

        line = rx.sub(apply, line)
    return line


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Redact subscriber/dialog identifiers from a log."
    )
    ap.add_argument("input", nargs="?", type=Path, help="log file, or - for stdin")
    ap.add_argument("-o", "--out", type=Path, help="output file (default stdout)")
    ap.add_argument("--check", action="store_true",
                    help="write nothing; exit 1 if anything would be redacted")
    ap.add_argument("--show-changes", type=int, default=0, metavar="N",
                    help="print up to N example lines per rule (to stderr)")
    ap.add_argument("--keep-ipv6-prefix", type=int, default=0, metavar="N",
                    help="keep the first N IPv6 hextets (default 0: redact all)")
    ap.add_argument("--list-rules", action="store_true")
    args = ap.parse_args()

    if args.list_rules:
        for name, rx, _ in RULES:
            print(f"{name:10s} {rx.pattern[:70]}")
        return 0

    global KEEP_V6_PREFIX
    KEEP_V6_PREFIX = max(0, args.keep_ipv6_prefix)

    if args.input is None:
        ap.print_help()
        return 1

    if str(args.input) == "-":
        src, close = sys.stdin, False
    else:
        try:
            src = args.input.open("r", errors="replace")
        except OSError as e:
            print(f"cannot read {args.input}: {e}", file=sys.stderr)
            return 2
        close = True

    if args.out and str(args.input) != "-" and args.out.resolve() == args.input.resolve():
        print("refusing to overwrite the input file in place", file=sys.stderr)
        return 2

    counts: dict[str, int] = {}
    samples: dict[str, str] = {}
    out_lines = [redact_line(line, counts, samples) for line in src]
    if close:
        src.close()

    total = sum(counts.values())

    if args.check:
        if total:
            print(f"{total} identifier(s) would be redacted:", file=sys.stderr)
            for name, n in sorted(counts.items(), key=lambda kv: -kv[1]):
                print(f"    {name:10s} {n}", file=sys.stderr)
            return 1
        print("clean", file=sys.stderr)
        return 0

    text = "".join(out_lines)
    if args.out:
        args.out.write_text(text)
        dest = str(args.out)
    else:
        sys.stdout.write(text)
        dest = "<stdout>"

    print(f"redacted {total} occurrence(s) -> {dest}", file=sys.stderr)
    for name, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"    {name:10s} {n}", file=sys.stderr)
    if total == 0:
        print("    (nothing matched: check the log is what you think it is)",
              file=sys.stderr)

    if args.show_changes:
        print("\nexample source lines per rule:", file=sys.stderr)
        for name in sorted(samples)[: args.show_changes]:
            print(f"    [{name}] {samples[name]}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
