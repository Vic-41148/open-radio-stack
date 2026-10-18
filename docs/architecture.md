<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Samsung M52 5G Radio Stack: Architecture Atlas

Part of the **Open Radio Stack** research dossier. Device: Samsung
Galaxy M52 5G (`m52xq`, ~`r0q` platform), Snapdragon 778G (SM7325),
shipped Samsung One UI / UN1CA. SIM-era baseband (kodiak) is signed
Hexagon firmware and is NOT analyzed here. This dossier covers the
userspace radio stack only.

Everything below was recovered by static reverse engineering (Ghidra/
REA on shipped binaries) cross-checked against live evidence from a
rooted device running UN1CA 3.2.0 with a VoLTE-and-5G SIM in India.
No proprietary code, blobs, or strings reproduced here beyond short
factual log identifiers needed to match behavior in the field.

---

## 1. Layer map (top to bottom)

```
Android framework (Telephony/IMS service)
  └─ ims daemon (SAP: com.sec.imsservice)  ← Carrier profile store
       ├─ RegistrationGovernor / PdnController (public CTS APIs only)
       ├─ FlatBuffer request builders (per-request structs)
       └─ native client shim
            └─ libsec-ims.so  ← reSIProcate SIP UA + Samsung managers
                 SafetyVoice/DTC: CallManager/CallSession/CidManager/etc.
                 Security/Ips: Security-Server parse → PF_KEYv2 install
                 DnsManager: c-ares per-network NAPTR/SRV/A/AAAA
                 ImsSmsManager: SIP MESSAGE SMS carrier
       └─ rild → libsec-ril.so  ← vendor RIL
            ├─ QMI over QRTR/MHI (no qmuxd, QCRIL stubbed)
            │    WDS (data), IMSS (IMS), NAS, DMS, DSD, DPM
            ├─ DataCallManager: generic DoSetupDataCall + reject
            │    taxonomy + (newer bases) explicit IMS gate
            └─ radio HAL (AIDL/HIDL 1.x alignment; UN1CA = 1.6-gen)
  └─ audio HAL: adev_set_mode honors modes; modem voice path used
```

Platform facts closed for SM7325:

| Question | Answer |
|---|---|
| RIL transport | QMI over QRTR/MHI, `qrtr.ko`, `vendor.qrtr-ns` |
| qmuxd | absent (image + process table) |
| QCRIL | stubbed via `rild-dummy` init overrides |
| IMS bearer request | Android-side (`SETUP_DATA_CALL` on IMS APN), no modem-native attach |
| VoLTE MBN | none in India; runs on common/ROW defaults; carrier policy 100% Android-side |
| audio | no lottery: `adev_set_mode` honors IN_CALL; modem voice path |
| radioHAL generation | stock-era CYD2 = 1.5; UN1CA = 1.6-gen (pduSessionId) |

## 2. Data-path truth

- IMS PDN comes up like any other APN: framework issues
  `SETUP_DATA_CALL` with the IMS APN; RIL runs
  `DataCallManager::DoSetupDataCall` → QMI `WDS::StartNetwork` with
  the profile baked by `SetStartNetworkParam`.
- Reject reason you'll see is NEVER "older-grims-sync-style ePCS
  refuses IMS": your failures are generic (CID exhaustion, state
  rejects, `MISSING_UNKNOWN_APN`) unless your base ships the newer
  explicit gate:
  `DCM-Reject IMS data call, as PS not regi or not eHRPD, LTE.`
  Gate opens on regState ∈ {registered-at-PS; and (eHRPD; or
  LTE-with-5G-enabled)} per the decision tree in `ims-pdn.md`.
- CID model: IMS bearer is **CID 2 by convention**;
  `ImsPdnTriggered` == "call slot 2 connecting-or-connected".
- CID allocation: slot scan with attach-CID exclusion (+0x5f0
  strides), no instant reject (A226B's 4 ms behavior does NOT
  transfer to this platform).

## 3. SIP-layer truth

- SIP UA = reSIProcate, statically resident in `libsec-ims.so`.
  Samsung's managers SIT ON resip; `SipStack::send/post` are stock
  (verified in binary).
- REGISTER: `RegistrationManager::TryRegister` (alloc session, post
  event 0x65); 401 challenge → AKA response build (digest fields).
  Java `RegistrationRequestBuilder` passes FlatBuffer fields:
  instance-id (`+sip.instance`), session-expire, contact extras.
- MO 3GPP VoLTE: `CallSession::DoMakeCall` assembles resip
  NameAddr/Uri, gates on profile (precondition/UAC/DSDS/CMC),
  ACB check first, then `BaseDialog`.
- MT: `CallSession::NotifyIncomingCall` builds `IncomingCall` event
  (id 0x2715) from INVITE: Call-ID, From, P-Asserted-Identity,
  History-Info, display name, peer URI, SDP call type →
  `BaseSession::OnNotify` → `VolteNotifier.onIncomingCall`.
- SMS over IMS: native `ImsSmsManager::OnIncomingImsSms` handles
  SIP MESSAGE: MESSAGE-only, "SMSIP not registered → 488" guard,
  `In-Reply-To` Call-ID dedup, ContentType type/subtype, payload
  hex-passthrough, rp-ack correctness (unknown Call-ID → 488).

## 4. Security (RFC 3329) and kernel handoff

- No key derivation exists in native: AKA IK/CK pass from Java as
  opaque strings; native stores them.
- `RegiConnecting::UpdateInfoForIPSec` parses `Security-Server` from
  the challenge, picks the common mechanism (q-value, auth/encr algs,
  client/server SPIs). No common mechanism → continue unsecured.
- Install path = **PF_KEYv2** raw socket
  (`socket(AF_KEY, SOCK_RAW, 2)`, refcounted static singleton), NOT
  netlink/xfrm: `IPSecInterface` ops = SetSAKey(+Auth), ApplySAAssoc,
  ApplySAPolicy, OperateOnSAD/SPD. Cipher enum IDs observed:
  3 / 12 / 20 / 11 (string→enum map in `SetIPSecInformation`).

## 5. P-CSCF discovery (explicit priority)

`profile.pcscfPreference` selects the source:

| pref | source |
|---|---|
| 0 | PCO from the IMS PDN LinkProperties (default for Airtel etc.) |
| 1 | ISIM (A38 `getIsimPcscf`) |
| 2 | static carrier profile list |
| 3 | RCS policy manager |
| 4 | RCS policy manager (not RCS-only tasks) |
| 5 | OMA-DM provisioning |

Domain-shaped entries then go through DNS: NAPTR
(`needNaptrDns`) → SRV `_sip._tls.<host>` → A/AAAA, native c-ares
with instant AF_INET6→AF_INET retry (100 ms) plus a second-chance
`PerformIpV4Fallback`. Chosen P-CSCF (addr list + port) lands in the
FlatBuffer `RequestRegistration`.

## 6. UN1CA vs stock deltas (same device, different AP)

Refreshable diff table (strings only, no code shipped):

- UN1CA RIL = radio-HAL **1.6 generation** (`OEM_ALLOCATE_PDU_SESSION_ID`, explicit HAL-1.6-handover log)
- **VoNR** support present only in UN1CA (handler family + `RxVonrNotPossibleInd`)
- N1-mode (NR/S1) requests present only in UN1CA
- Samsung QUANTUM security IPC added (encrypted-messaging channel)
- PCSCF-restoration broadcast path updated
- KOR/FlexCS CSCFeatures stripped in UN1CA build

Consequence for custom-ROM work: stock-era RIL stays AOSP radio-HAL
1.5-compatible; expect zero help from Samsung-side blobs when AOSP
newer HAL features need wiring around +0x100000 unknown symbols.

## 7. Files

- `architecture.md` (this file)
- `ims-pdn.md`: data-call gate + reject taxonomy + WDS field map
- `carrier-config.md`: Airtel profile semantics (McMnc-driven)
- `README.md`: methodology, scope, legal/config cautions
