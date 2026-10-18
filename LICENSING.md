<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Licensing

Two licences, split by what a file is:

| Material | Licence |
|---|---|
| Prose: every `*.md` file: `docs/`, `device/`, `evidence/`, `README.md`, `ROADMAP.md`, this file | `CC-BY-4.0` |
| Scripts and machine-readable config: `tools/*.sh`, `tools/*.py`, `.gitignore`, any future `.xml`/`.json` | `MIT` |
| Patches, which are derivative of the project they patch: `patches/*.patch` | the licence of that project: `GPL-2.0-only` today |

Full texts are in `LICENSES/`. Every file also carries its own tag, so
it stays correctly licensed when you copy it out of here:

<!-- REUSE-IgnoreStart -->
```
SPDX-License-Identifier: CC-BY-4.0     markdown
SPDX-License-Identifier: MIT           scripts, config
SPDX-License-Identifier: GPL-2.0-only  patches
```
<!-- REUSE-IgnoreEnd -->

## Why this split

- **The documents are the point, and prose wants a prose licence.**
  `CC-BY-4.0` lets anyone quote, mirror, translate and build on the
  findings as long as they credit them. Copyleft on a description
  mostly stops people quoting it.
- **The scripts are meant to be dropped into someone else's tooling.**
  `MIT` is compatible with `Apache-2.0` trees (LineageOS device trees,
  AOSP) and with `GPL-2.0` projects alike. `GPL-3.0` (which this repo
  carried briefly) is compatible with neither of those, and would
  have kept the redactor out of the CI of the people most likely to
  need it.
- **Attribution is the whole obligation.** If you publish something
  built on this, name the work, credit `Vic-41148` and link back here.
  Say so if you changed anything. That is all `CC-BY-4.0` asks.

## Contributing

Corrections with evidence are welcome: see `README.md`. GitHub's terms
license a contribution under the licence the repo already carries, so
a documentation fix arrives under `CC-BY-4.0` and a script fix under
`MIT`. Nothing else is asked of you.

## Patches to other projects

`docs/upstream-findings.md` describes defects found in apps that are
`GPL-2.0-only`. A patch against such a project belongs to that project
and stays `GPL-2.0-only`: `patches/` holds those, each with its own
tag and `.license` sidecar, kept apart from the `CC-BY-4.0` and `MIT`
material. No source from those projects is redistributed here: the
findings describe behaviour, protocol layout and log lines.

## Not here

- **No vendor code.** No firmware, no Samsung or Qualcomm binaries, no
  decompiled dumps, no signing material, no MBN files, no APK copies.
- **No personal data.** No IMSI, IMEI, MSISDN, ICCID, subscriber
  address or dialog identifier. Published logs are redacted; run
  `tools/redact-log.py --check` on anything you take from a device.
- **No authorship claimed** over the projects listed in `NOTICES.md`.
