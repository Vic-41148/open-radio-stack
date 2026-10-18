<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# evidence/: what backs the claims

Every behavioural claim in `../docs/` is either a fact with a named
source or explicitly marked as an inference. This directory is where
the named sources go.

## What belongs here

| Folder | Contents |
|---|---|
| `traces/` | Trimmed log and packet excerpts: the signal-relevant lines only, redacted. |
| `decompiles/` | Pseudocode excerpts actually cited by a docs page, plus the binary hash they came from. |
| `tool-notes/` | Outputs of `../tools/`, and notes on how a capture was taken. |

## What never belongs here

- Firmware, extracted vendor binaries, APKs, MBN files, signing
  material.
- Unredacted captures: no IMSI, IMEI, MSISDN, ICCID, subscriber or
  server addresses, SIP URIs, Call-IDs or dialog identifiers.
- Whole session logs. Trim to the lines that carry the claim, then run
  `../tools/redact-log.py` and check the result.

## Why this folder is empty of traces right now

The raw corpus behind this work is large and personal: full radio logs,
SIP dialogs, packet captures and firmware material from a real
subscriber line. It stays private. What is published is the analysis,
with the mechanism re-stated in a form that anyone can verify on their
own device using `../tools/`.

So this directory is a place for *contributions*: if you reproduce a
finding, or contradict one, a redacted excerpt here (or in an issue) is
worth more than a prose report. Say which docs page it supports or
refutes, and which command produced it.
