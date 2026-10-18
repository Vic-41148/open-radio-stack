<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Third-party notices

This repo redistributes no third-party code. The projects below are the
ones this work depends on, cites, or contributes back to. Licences were
checked in 2026-10; entries marked *unverified* were not read at the
source. Read the project's own `LICENSE` before relying on any of it:
this table is a pointer, not legal advice.

## Projects this work builds on

| Project | Role here | Licence (2026-10) |
|---|---|---|
| `phhusson/ims` (PhhIms) | The open IMS app. Built, signed and installed to get the result in `docs/open-ims-on-gsi.md`. One build fix is worth sending back. | `GPL-2.0-only` |
| `krazey/ims` | Fork of the above and the base actually used. The RP-ACK defect found here was fixed and filed upstream. | `GPL-2.0-only` (inherited) |
| AOSP `platform/packages/modules/ImsStack`, `ImsMedia` | The upstream userspace IMS stack; architecture reference. | `Apache-2.0` |
| `krazey/ImsStack`, `krazey/ImsMedia`, `krazey/CarrierSettings` | Community ports of the above to Samsung devices; an alternative integration route, not used in the result here. The carrier-settings extension **mixes** its `Apache-2.0` baseline with generated data derived from `GPL-2.0-only` PhhIms data. | `Apache-2.0`, mixed for the carrier extension: read at the source, link to it, do not copy it here |
| `libqmi` | QMI message reference. | library `LGPL-2.1-or-later`; `qmicli` and the other tools `GPL-2.0-or-later` |
| ModemManager, `81voltd` (postmarketOS) | Prior art for the IMS data service on Qualcomm modems. | unverified |
| `sbaresearch/mbn-mcfg-tools` | MBN extraction, used to establish that no IMS policy lives in the modem config files on this platform (`tools/scan-mbn-ims.py` is the scan written for that finding). | unverified |
| QCSuper, SCAT | Qualcomm DIAG capture and parsing for the signalling work. | unverified |
| LineageOS device trees and kernel for `m52xq` / `sm7325` | The ROM side. Other people's work; this repo documents the layer beneath it. | see LineageOS |

## Code derived from other projects

`docs/upstream-findings.md` item 1 describes a change to code that is
`GPL-2.0-only`. A patch written against it inherits that licence, and
`GPL-2.0-only` does not combine with `GPL-3.0-only` or with the `MIT`
material in `tools/`. That patch is therefore in `patches/` under its
own header, never merged into the rest of the tree, and the `GPL-2.0`
text vendored for it is `LICENSES/GPL-2.0-only.txt`. The same applies
to anything taken out of an `Apache-2.0` project.

This repo's own material is `CC-BY-4.0` (prose) and `MIT` (scripts),
and the patches in `patches/` are `GPL-2.0-only`: see `LICENSING.md`.

## Vendor names

Samsung, Qualcomm, Android and the carrier names mentioned are
trademarks of their owners and are used descriptively only.
