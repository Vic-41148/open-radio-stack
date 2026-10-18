<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Open Radio Stack: Samsung Snapdragon phones

How the proprietary userspace radio stack on a Samsung Snapdragon
phone actually works (vendor RIL, IMS PDN, SIP registration, call
audio, carrier policy) and how to replace the closed IMS app with an
open one so VoLTE, IMS SMS and VoWiFi work on a custom ROM.

**Reference device:** Samsung Galaxy M52 5G (`m52xq`, SM7325 /
Snapdragon 778G) with an Airtel India SIM.
**Method:** static reverse engineering of shipped userspace binaries
(Ghidra + REA), cross-checked against live captures from a rooted
device the author owns.

## Status

| Device | SoC | Modem | State |
|---|---|---|---|
| Galaxy M52 5G (`m52xq`) | SM7325 | Qualcomm | **VoLTE MO+MT, IMS SMS MO+MT, DTMF, call teardown proven on a GSI**: an open ImsService (`me.phh.ims`) drives the whole chain, and the vendor RIL accepts the IMS data call. See `docs/open-ims-on-gsi.md`. |
| Galaxy A22 5G (`a226b`) | MT6833 | MediaTek | Not worked on in this repo. Prior notes summarised in `device/a226b/README.md`. |
| Any other Samsung Snapdragon | - | - | Not started. `docs/porting-guide.md` lists what a port needs. |

Milestone-by-milestone progress: `ROADMAP.md`.

## What is proven here

On the M52, with an open ImsService on a LineageOS 21 GSI:

- The framework requests the IMS APN with a standard
  `SETUP_DATA_CALL` and the **vendor RIL accepts it**
  (`cause=NONE`, `cid=2 ifname=rmnet_data1`). No device-specific
  workaround, no modem-native attach.
- P-CSCF arrives over PCO on the IMS PDN.
- Full AKA (AKAv1-MD5) + IPsec REGISTER → `200 OK`, `registered=true`.
- **VoLTE calls, mobile-originated and mobile-terminated**, with
  two-way RTP audio (AMR-NB 12.2k, and AMR-WB on the MT call),
  in-dialog re-INVITE, DTMF and `BYE` teardown.
- **SMS over IMS, both directions.** Inbound SMS turned out to hit a
  real defect in the IMS app (the RP-ACK echoed the wrong reference);
  root cause, proof and fix: `docs/upstream-findings.md`.

## What is in scope

- `libsec-ril.so`: vendor RIL, QMI over QRTR/MHI. Reject taxonomy and
  the explicit IMS gate, field-level.
- `libsec-ims.so`: reSIProcate-based SIP UA plus Samsung's managers:
  registration, calls, SMS-over-IMS, IPsec, DNS.
- The Java glue (`com.sec.imsservice`) request shapes and the
  carrier/IMS profile selection chain.
- The open replacement path: build, sign, install and bind an open
  ImsService.
- Audio mode handoffs, read from userspace only.

## Out of scope, on purpose

- Modem/baseband firmware (signed Hexagon image). Not analysed, not
  patched, not redistributed.
- A full ROM build recipe. This repo documents the stack and the IMS
  app; the device tree is other people's work (`device/m52xq/`).
- Per-carrier personalisation beyond the observed Airtel India
  behaviour. See `docs/carrier-config.md`.

## Reading order

1. `README.md`: this page: scope, status, limits.
2. `docs/architecture.md`: the layer map, who owns what, platform Q&A.
3. `docs/ims-pdn.md`: data-call lifecycle, the IMS gate, QMI WDS map.
4. `docs/open-ims-on-gsi.md`: the open-stack proof and how to
   reproduce it on your own device.
5. `docs/carrier-config.md`: profile semantics, P-CSCF priority,
   pitfalls.
6. `docs/upstream-findings.md`: defects found in the open IMS apps,
   with the filed fix.
7. `patches/`: the filed RP-ACK fix, ready to `git am` into the IMS app.
8. `ROADMAP.md`: what is done, what is open.

## Field checks on a rooted Samsung

1. Transport: `ps -A | grep qrtr-ns`, `rild` present, `qmuxd` absent
   on this generation. `tools/check-qrtr.sh` automates it.
2. IMS-APN failures: match the log lines against `docs/ims-pdn.md`
   before blaming the carrier. Most "IMS broken" reports on custom
   ROMs are pre-gate generic failures, not carrier lockouts.
3. No VoLTE option at all: check CarrierConfig
   `carrier_volte_available_bool` first: that was the actual root
   cause on this device. See `device/m52xq/carrierconfig.md`.
4. Collecting evidence: `tools/collect-device-info.sh` gathers the
   read-only inventory, `tools/redact-log.py` strips identifiers
   before you share anything.

## Rules this repo lives by

- **Analysis, not artifacts.** No firmware, no extracted vendor
  binaries, no decompiled code dumps, no signing material, no
  unredacted captures. Everything personal is redacted before it
  lands here: IMSI, IMEI, MSISDN, ICCID, IP addresses, SIP URIs,
  Call-IDs, tags.
- **Read-only on the device.** No writes to EFS, NV, calibration or
  identity partitions. Diffing is enough.
- **Nothing touched the modem.** The baseband is out of scope, and no
  signalling experiment is ever run against a live network.
- **Emergency calling stays working.** Gate MMTEL emergency handling
  off while bringing a stack up; keep the circuit-switched path.

Documents are `CC-BY-4.0`, scripts are `MIT`: see `LICENSING.md`, and
`NOTICES.md` for the projects this work builds on. The files in
`patches/` are the exception: they patch `GPL-2.0-only` code, so they
carry that licence and stay apart from everything else here.

## Contributing

Corrections with evidence are welcome, especially traces of the same
code paths on other Samsung Snapdragon devices: your redacted logs
either match the findings here or they don't, and both answers are
useful. Use the tools in `tools/` so the redaction rule is kept.
