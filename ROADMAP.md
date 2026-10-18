<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Roadmap and status

Last updated: 2026-10-19.

## Milestones

| | Milestone | State | Where |
|---|---|---|---|
| **M0** | Baseline: confirm the device, save the stock firmware, record what stock does | **Done**: model/region confirmed, stock firmware saved, stock baseline recorded (calls, SMS, VoLTE, 5G NR all work on stock) | `device/m52xq/` |
| **M1** | Inventory: which process owns which layer | **Done**: vendor `rild` + `libsec-ril` over QMI/QRTR-MHI, `qmuxd` absent, QCRIL stubbed | `docs/architecture.md` |
| **M2** | Golden trace: one annotated successful call | **Done**: stock setup and an ACTIVE call annotated; later, the open-stack wire trace | `docs/open-ims-on-gsi.md`, `docs/ims-pdn.md` |
| **M3** | Carrier config | **Done, hypothesis inverted**: no IMS policy lives in the modem MBN files on this platform; the lever is Android-side CarrierConfig plus runtime QMI IMSS provisioning | `docs/carrier-config.md` |
| **M4** | Open IMS running on the device | **Reached on a GSI, not in-ROM**: VoLTE MO+MT, IMS SMS MO+MT, DTMF, teardown all proven with an open ImsService on a LineageOS 21 GSI. An in-ROM Lineage build with the same stack is still open | `docs/open-ims-on-gsi.md` |
| **M5** | How the IMS bearer is created | **Done**: the framework requests the IMS APN as a normal data call and the vendor RIL accepts it; P-CSCF arrives via PCO. No device-specific workaround needed | `docs/open-ims-on-gsi.md` §4 |
| **M6** | Generalise to a second device | **Not started**: no second Samsung Snapdragon has been through it | `docs/porting-guide.md` |

## Open items

| # | Item | State |
|---|---|---|
| 1 | In-ROM Lineage build with the open IMS stack (the real M4) | Not started. Needs the device tree plus overlay, sepolicy and audio integration in ROM. Build against a pinned ImsStack / ImsMedia / CarrierSettings trio and record the SHAs in the build notes; the PhhIms route used on the GSI is the older one. |
| 2 | Live QMI signalling trace of a VoLTE call | Partial. DIAG is reachable with root and static queries work, but streaming capture is silent, so the radio-side view is still missing. |
| 3 | A second device (M6) | Not started. No public IMS work on the M52 or on SM7325 has been found; the quickest way to close this is to ask whether anyone else is on that SoC, then run `docs/porting-guide.md`. |
| 4 | VoWiFi (IWLAN/ePDG) | Not implemented in the open IMS app used here. |
| 5 | ViLTE | Not implemented. |
| 6 | Second carrier | Everything here is one carrier in one country. Registration behaviour is carrier-dependent. |
| 7 | Upstream: items 2–4 of `docs/upstream-findings.md` | Unfiled. Item 1 is filed as a PR. A patch against PhhIms or krazey is GPL-2.0-only (see `NOTICES.md`), so it cannot be merged into the `tools/` tree. |
| 8 | `phhusson/ims`: the one-character compile fix | Unfiled. It is the only change worth sending to that repo. |
| 9 | Publish the filed RP-ACK fix so it can be applied now | Not started. It belongs in `patches/` under a GPL-2.0-only header, so a ROM builder can use it before the upstream PR merges. |

## How this list gets shorter

Items 1 and 3 are the two that change the shape of the project: an
in-ROM build proves the stack survives outside a GSI, and a second
device turns the findings from a device anecdote into a platform
claim. Everything else is a test or a report.
