<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Open IMS on a GSI: the full bring-up

**Result:** the closed Samsung IMS app is not required for VoLTE on
this device. An open ImsService, installed on top of a stock-ish
LineageOS 21 GSI, drives the complete chain: the framework requests
the IMS bearer, the vendor RIL accepts it, SIP registers over AKA +
IPsec, and voice and SMS work in both directions.

This page is the reproducible version. Values that identify a
subscriber, a server address or a dialog have been redacted.

## 1. What had to be true for this to work

| Requirement | Why |
|---|---|
| An open `ImsService` bound as the slot-0 MMTEL service | The framework only requests an IMS bearer for a feature that a real ImsService has reported READY. This was the missing piece. |
| The APK signed with the **platform** certificate | The manifest needs `sharedUserId="android.uid.system"`; `BIND_IMS_SERVICE` and `READ_PRIVILEGED_PHONE_STATE` are signature permissions. |
| `config_ims_mmtel_package` pointing at it | Camera-ready config for MMTEL. See §3. |
| An IMS APN in the carrier's APN list | The framework requests the IMS APN like any other data call. |

Everything else (`IRadioIms`, a vendor IMS HAL, QTI's `imsd`, Samsung's
`secims`) turned out **not** to be required. That is the surprising
part of this result.

## 2. Build

Source: `krazey/ims` (a fork of `phhusson/ims`), package id
`me.phh.ims`.

Toolchain that worked: JDK 17, Android SDK `platforms;android-33`,
`build-tools;33.0.2`, `ndk;25.1.8937393`, CMake 3.22.1.

Two build facts worth knowing before you start:

1. **Use a real framework jar.** The `app/libs/android.jar` checked
   into the tree is not sufficient to build it. Build against a full
   AOSP API-34 `android.jar` (the class that matters is the
   non-public `MmTelFeature` implementation) and pass it explicitly,
   e.g. `-PplatformApiJar=/path/to/aosp-android-34.jar`.
2. **AOSP test keys are the platform keys here.** Sign with
   `platform.x509.pem` / `platform.pk8` and `signapk.jar`. Verify
   before installing that the signer matches the ROM's own platform
   cert (compare against a system app such as `TeleService.apk`); if
   it does not match, the install will succeed and the service will
   never be bound.

## 3. Install and bind

A read-only `system-as-root` GSI has no writable `/system`, so there
is no module route. Because the APK carries the platform signature, a
plain data install is enough and it runs as `uid 1000`:

```sh
adb install -r -g PhhIms.apk
```

Then point the MMTEL config at it. The usual route is an RRO overlay
whose value is:

```
config_ims_mmtel_package = "me.phh.ims"
```

Two traps:

- Vendor overlays for `org.codeaurora.ims` (if present) are **immutable
  preinstalls**. Priority decides the winner, so give the open-IMS
  overlay maximum priority rather than trying to disable theirs.
- `ImsResolver` caches the resolved config in `system_server`. After
  enabling the overlay, a full reboot picks it up, or, if you cannot
  reboot, a framework restart does:

```sh
adb shell stop ; adb shell start
```

Success looks like this:

```
ImsResolver: ImsServiceController added on slot: 0 with feature: MMTEL
             using package: ComponentInfo{me.phh.ims/...}
ImsServiceController: notifyImsFeatureStatus: slot=0, feature=MMTEL, status=READY
```

## 4. The chain, in order

### 4.1 The framework requests the IMS bearer

```
ConnectivityService: requestNetwork ... Capabilities: IMS&TRUSTED&NOT_VPN
                     ... RequestorPkg: <ims app>
DNC-0: onSetupDataNetwork: dataProfile=[ApnSetting] DEFAULT IMS ...,
       IPV4V6, TrafficDescriptor={mDnn=ims}, network type=LTE, reg state=HOME
```

### 4.2 The vendor RIL accepts it

This is the point the prior expectation got wrong. There is no
IMS-specific refusal on this RIL; the generic `DoSetupDataCall` path
runs and succeeds:

```
RILJ: [0239]> SETUP_DATA_CALL ... apn=ims ... accessNetworkType=EUTRAN
RILD: CopyDataReqData, setup_data_call
RILD: DCM-NotifyDataCallState: 4 for CID 2 SessionId 256
RILJ: [0239]< SETUP_DATA_CALL DataCallResponse: { cause=NONE(0x0)
              cid=2 ifname=rmnet_data1
              addresses=[2401:4900:<redacted>/64]
              pcscf=[/2401:4900:<redacted>, /2401:4900:<redacted>] }
DNC-0: IMS data state changed from DISCONNECTED to CONNECTED.
```

**P-CSCF arrives in the setup response** (PCO), not from a config file.
That single fact removes a whole class of "carrier config" guesses.

### 4.3 A bring-up race to expect

On the first attempt the PDN was reported connected while its netdev
was not up, so nothing could leave the phone:

```
ip link: rmnet_data1@...: <> ... state DOWN        (no kernel address)
netd: interface configuration error 64 ("Machine is not on the network")
```

The socket to the P-CSCF sat in `SYN-SENT`, `tcpdump` on the interface
saw zero egress, and the call was torn down. On retry the bearer came
up on a second interface fully configured and everything worked. If
you see this, tear down and let it re-request; do not chase it as an
IMS bug.

### 4.4 REGISTER: 401 → AKA → IPsec → 200

```
> REGISTER sip:ims.mnc<MNC>.mcc<MCC>.3gppnetwork.org SIP/2.0
> Security-Client: ipsec-3gpp;prot=esp;mod=trans;
    spi-c=...;spi-s=...;port-c=...;port-s=...;ealg=null;alg=hmac-sha-1-96
< SIP/2.0 401 Unauthorized
    Www-Authenticate: ... algorithm=AKAv1-MD5, qop="auth"
    Security-Server: ipsec-3gpp; q=0.1; alg=hmac-md5-96; ealg=null; ...
> REGISTER ... Security-Verify: ... Authorization: ... algorithm=AKAv1-MD5
< SIP/2.0 200 OK
    Contact: <sip:...>;...+g.3gpp.smsip;audio;expires=7200
```

The AKA challenge is answered from the SIM (the app requests it from
the framework); no key material is handled in userspace. `expires`
matched the carrier's IMS profile value exactly, which is a good
cross-check that the profile layer is being read correctly.

### 4.5 IPsec lands in the kernel

Four transport-mode ESP SAs, integrity-only (`hmac-md5-96`,
`ealg=null`), installed by `netd` on the app's request:

```
netd: ipSecAllocateSpi(1000, "", <ue-addr>, 0)
ip xfrm state  → 4 × proto esp, reqid 1000, auth hmac(md5), enc ecb(cipher_null)
```

The frames themselves match the static finding from the RE work, so
the wire and the decompilation agree.

### 4.6 Registration is visible to the framework

```
ImsPhone: [0] updateDataServiceState: ... mVoiceRegState=0(IN_SERVICE)
SST: setImsRegistrationState: {registered=true ...}
```

### 4.7 Voice

- **MO call** placed and answered, two-way RTP, `AMR-NB 12.2k`.
- **MT call** answered, two-way RTP, `AMR-WB` at 16 kHz.
- In-dialog `re-INVITE`, DTMF, and remote `BYE` → `200` teardown all
  behaved; the encode thread exited cleanly after
  `totalPacketsSent=1833` on the observed call.

### 4.8 SMS over IMS

A SIP `MESSAGE` carrying an RP-DATA is decoded and acknowledged in the
same dialog:

```
PHH SipSms: SMS from <redacted> to <redacted>, pduLen 93
PHH SipHandler: Decoded SMS type RP_DATA_FROM_NETWORK
PHH SipHandler: Replying back with SIP/2.0 200 OK
```

Inbound SMS is where a real bug lived in the open app: the
acknowledgement carried the wrong reference and the carrier's message
centre rejected it. See `upstream-findings.md`.

## 5. What this does not prove

- **VoWiFi (IWLAN/ePDG)**: not implemented in the open app used here.
- **ViLTE**: not implemented.
- **Emergency calls over IMS**: deliberately out of scope; keep the
  circuit-switched path as the safety net while bringing a stack up.
- **Carrier certification.** One device, one carrier, one SIM.
- It does **not** mean every Samsung Snapdragon behaves like this. The
  RIL behaviour that made it easy here is a property of this platform
  and this RIL generation; check yours with `tools/check-qrtr.sh` and
  the log lines above.
