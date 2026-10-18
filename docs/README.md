<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# docs/: index

| Page | What it answers |
|---|---|
| `architecture.md` | Which process owns which layer, what the vendor stack looks like on this platform, and the platform questions (RIL type, transport, IMS PDN bring-up, audio, carrier config) answered from the binaries. |
| `ims-pdn.md` | The data-call lifecycle: the generic reject taxonomy, the explicit IMS gate, and the QMI WDS parameter map. Start here when an IMS APN will not come up. |
| `open-ims-on-gsi.md` | The open-stack result: build, platform-sign, install and bind an open ImsService, then the full bring-up (IMS PDN → P-CSCF → AKA/IPsec REGISTER → VoLTE → SMS). Includes the exact commands and the log lines to expect. |
| `carrier-config.md` | Carrier and IMS profile selection, the fields that matter, what triggers re-REGISTER, and the pitfalls that break registration on custom ROMs. |
| `upstream-findings.md` | Defects found in the open IMS apps while doing this work, with the filed fix. |
| `audio.md` | The call audio path from the IMS app down to the vendor audio HAL, and what is known to work. |
| `porting-guide.md` | What a second Samsung Snapdragon device needs, in order, with the checks that decide whether it is a one-day job or a project. |

Method notes are in the pages themselves. Reusable scripts are in
`../tools/`, device-specific material in `../device/`.

## How claims are written

- **Fact**: recovered from the binary or the wire, with the evidence
  named (report, function, log line).
- **Inference**: reasoned from facts, marked as such.
- Anything not verified carries the same marker on the page. There is
  no third category: no "probably works".
