<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Carrier-Config Semantics (Samsung IMS, observed on Airtel India)

McMnc-driven selection observed end to end on UN1CA with an Airtel
SIM, cross-checked against the decompiled `imsservice` app.

## 1. Selection chain

`mccmnc 40410` → operator map `AIRTEL_IN` → IMS profile
`AIRTEL VoLTE` → SWA governor (Samsung's SW-Auto-`
AntiThrottle` variant `governor.samsung`).

No India MBN: the modem runs common/ROW defaults. Every IMS-related
policy is Android-side; you will NOT find "VoLTE-India" in modem
NVRAM; you will find it in one of:

- IMS profile table (Java, `com.sec.imsservice`)
- `CscFeature` overlay values (only some are pop­ulated)
- runtime PCO / ISIM - sourced values

## 2. Profile fields observed on AIRTEL VoLTE

- registration_expires: 14400 s
- session_expires: 7200 s (min-SE honored)
- precondition: on (mandatory QoS)
- ipsec: on but only if challenged (Security-Server)
- PCSCF: **preference 0**: network-provisioned over PCO
  (live capture: `/2401:4900:…` from LinkProperties on IMS PDN)
- smsip: on; DTMF: on; video-capable: no

## 3. Reconfig costs (what triggers re-REGISTER)

`updatePcscfIpList` logic: if the current P-CSCF still present in
the refreshed list, keep it (optionally full revert per governor);
whole new set → `setDeregiReason(8)` + deregister + re-REGISTER.
VZW-specific: `sendReRegister` path. T-Mobile/OrangeGPG: reset
retry state instead.

## 4. Pitfalls for a custom ROM

- Do NOT ship an "india-volte.txt" XML that overwrites what
  `AIRTEL VoLTE` already handles: Samsung's stack comes up
  NORMALLY with the default profile; gadget-crafted overrides
  usually BREAK registration (e.g., wrong IPsec "always-on" vis)
- IMS-APN is set up like any other APN. If it fails, check
  CarrierConfig `KEY_CARRIER_VOLTE_AVAILABLE_BOOL` and the
  Samsung governor state, NOT an "IMS-only blob" test.
- fimsswitch / profsfer: Samsung re-reads on boot-slot change.
