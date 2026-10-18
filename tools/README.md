<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# tools/: check the claims, walk the same path

Small, dependency-light scripts. Every one of them operates on **your
own device** or **your own extracted files**: nothing here downloads or
ships vendor code, blobs or keys.

| Tool | What it does |
|---|---|
| `collect-device-info.sh` | Read-only inventory of a Samsung phone's radio stack: props, telephony services, vendor HALs, vintf entries, init scripts, transport processes. Start here on a new device. |
| `check-qrtr.sh` | Confirms how the RIL talks to the modem: QMI over QRTR/MHI (modern) versus legacy qmux or an AT tty. Positive and negative checks, with an exit status. |
| `dump-ril-symbols.sh` | Symbol inventory of a RIL binary you extracted yourself, for pre-flight addressing checks. |
| `scan-mbn-ims.py` | Scans firmware MBN/mcfg files for IMS-related configuration strings: the check that establishes whether VoLTE is configured modem-side at all. Includes a two-file diff mode. |
| `redact-log.py` | Strips subscriber and dialog identifiers from a log before you share it. This repo's redaction rule, as a tool. |
| `rea-address-cheatsheet.md` | The addressing discipline for Ghidra/REA work on these libraries. Read before trusting any address. |

## The order to run them

On a new device: `collect-device-info.sh`, then `check-qrtr.sh`, then
`scan-mbn-ims.py` against the firmware you extracted. That answers the
first three questions in `../docs/porting-guide.md` without changing
anything.

Before sharing any log: `redact-log.py`. Check it worked with
`--check` (exit status 1 means it found something) and read the
`--show-changes` output rather than trusting it blindly.

## Rules for anything added here

- Read-only against a device. No writes to EFS, NV, calibration or
  identity partitions.
- No vendor code, no binaries, no keys, no trace uploads.
- If a script needs a vendor binary, it takes a path to one **you**
  extracted. It never fetches one.

## Try it

`redact-log.py` has no dependencies beyond Python 3. Sanity check:

```sh
printf 'imsi 123456789012345 sip:+15550001234@ims.example.org\n' \
  | tools/redact-log.py -                 # -> imsi <id> sip:<number>@ims.example.org
```
