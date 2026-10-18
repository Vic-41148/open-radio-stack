<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# IMS PDN + Setup-Data-Call Truth

Atlas: reject taxonomy and the explicit IMS gate, field-level.

## 1. Generic reject taxonomy (all Samsung SM7325 RILs)

From full-blob decompilation of `DataCallManager::DoSetupDataCall`
(both SIM instances in the same binary): ten static reject
families, all keyed on request/CID/RIL state, none on "IMS" per se:

| Reject family | Trigger (simplified) |
|---|---|
| `MISSING_UNKNOWN_DIAL` etc. | null APN/addr, unresolved |
| cid busy / cid mismatch | CID already connecting/connected |
| requestInProgress | SetupDataCall already running |
| dataSwitch state | no radio exposed |
| insufficient cid slots | scan stranded |
| transport-level | mux/socket error |
| profile-type invalid | profile IRatioConvert map fails |
| LCP/nas error | transport retries stale |
| radio-off | radio state out |
| gate (explicit) | see §2 (newer bases) |

Practical debugging flow in any Samsung RIL build: log-string match
against the reject family, then check the *state* buffer path.

## 2. The explicit gate (UN1CA-lineage RILs)

Exact prelude logged before reject:
`DCM-Reject IMS data call, as PS not regi or not eHRPD, LTE.`

Conditions (decision tree recovered from the gate body):

- IMS attempted while `regState` does NOT equal
  `REG_REGISTERED-with-PS-data (LTE_HOME/ROAMING)` **and**
- transport is NOT eHRPD
- and the requested radio-access is LTE

Meaning: the gate opens when LTE PS is registered (or eHRPD at
CDMA), i.e., it's a status-ordering check, not a CarrierConfig
switch. If you see the string, your IMS registration hasn't
reached PS-Registered before the data call was placed.

## 3. QMI WDS `StartNetwork` field map

Param builder (`SetStartNetworkParam`). Recovered field identities:

- `profile_id` = baked from IMS profile (per `ConvertDataProfile`
  bitfield map: bit 9 → profile type `0x3e9` (IMSEmergency+),
  2/3/5 generic IoTs)
- `apn`, user/pass ← profile
- `tech_preference` ← radio access type
- `ip_family` ← IPv4v6 default on IMS
- auth protocol ← profile (PAP/CHAP)

CID database: `CidDbEditor::GetFreeCid` scan (attach-CID excluded,
strides via +0x5f0 records), `Dca::AllocateCall` wraps a
Dca-provided `DataAuth` + context (`ContextActivationDca::
DefineContext`), allocation result key = `MapDataCallSession`.

## 4. IMS instance / QMI service bind

`QmiImsService` binds `imss_get_service_object_internal_v01`
(service 1, version `0x5c`, instance count 6). IMSS requests carry
the FlatBuffer from Java: `RequestRegistration` includes
`pcscfAddrList`, `pcscfPort`, `ipsecParameters`, etc.

## 5. ePDG path

`LteEpdgDataCallManager` (third `DoSetupDataCall` instance address
@ 0x4780dc) runs the VoWiFi (unsynchronized ePDG) path; WiFi→LTE
handover is tracked inside it via `OnEpdnConnected`.
