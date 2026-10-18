<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Porting guide: a second Samsung Snapdragon device

Nothing here has been validated on a second device yet. This is the
order of checks that would turn a new device into either a one-day job
or a project, written from what the M52 taught us.

## Step 0: know what you are dealing with

```sh
tools/collect-device-info.sh            # read-only inventory
tools/check-qrtr.sh                     # transport
```

Four facts decide everything:

| Question | Why it decides the job size |
|---|---|
| Vendor RIL: `libsec-ril` (Samsung) or QCRIL (Qualcomm)? | The data-call path, and the reject style, differ. |
| Transport: QMI over QRTR/MHI, or legacy qmux sockets, or AT over a tty? | QRTR is the modern, easier case; the others change the tooling. |
| Does the platform have an IMS-specific gate in the RIL? | On the M52 it did not fire. On other bases there is an explicit `DCM-Reject IMS data call` keyed on registration state. |
| Does the shipped ROM ship `carrier_volte_available_bool=false`? | This was the actual root cause of "no VoLTE" here: a CarrierConfig flag, not a missing stack. |

## Step 1: establish a stock baseline

Before changing anything, record what the stock ROM does: calls, SMS,
VoLTE, VoWiFi, and the registration state. You cannot tell a missing
feature from a broken one without this.

## Step 2: static. Does an open ImsService suffice?

The M52 answered yes, and surprisingly easily: the framework requests
the IMS APN through the normal data-call path, and the vendor RIL
accepts it. That is not guaranteed on your device: a legacy data HAL
may reject the request style.

Test it cheaply before building anything: install an open ImsService on
a GSI (see `open-ims-on-gsi.md`), bind it as the MMTEL service, and
watch for:

```
ConnectivityService: requestNetwork ... IMS&TRUSTED&NOT_VPN
RILJ: SETUP_DATA_CALL ... apn=ims
RILJ: SETUP_DATA_CALL DataCallResponse: cause=NONE ...
```

- **Accepted + P-CSCF in the response** → you are on the M52 path.
  Continue to REGISTER.
- **Rejected** → you are in the harder case. Match the response
  against the reject taxonomy in `ims-pdn.md` before writing anything.
  A few ROMs have an overlay knob
  (`ims.request_ims_pdn_without_mmtel_bool`) for legacy data HALs that
  cannot attach MMTEL capability; treat that as a hypothesis to test,
  not a fix.

## Step 3: the open stack

Build, sign (platform certificate: verify against a system app), and
bind the open ImsService. Then work down this list and stop at the
first failure:

1. `ImsResolver` binds it as slot-0 MMTEL, status READY.
2. IMS PDN up, P-CSCF delivered via PCO.
3. 401 → AKA → IPsec → `200 OK`, `registered=true`.
4. MO call with two-way audio.
5. MT call.
6. SMS over IMS, both directions, **and check the RP-level
   acknowledgement, not just that a MESSAGE arrived.** That check is
   what `upstream-findings.md` item 1 is about, and "SMS arrived" is
   not enough to call it working.
7. DTMF, call waiting, teardown.

## Step 4: carriers

Repeat step 3 on a second carrier before claiming the device works.
Registration behaviour is carrier-dependent: P-CSCF delivery, IPsec
policy, the reference the SMSC validates, and profile values such as
session expiry all differ.

## What usually is *not* the problem

Ranked by how often it was the answer on this device:

1. CarrierConfig flags (the actual root cause here).
2. Missing ImsService (the second cause).
3. BR carrier/APN configuration.
4. Modem firmware: out of scope of this repo, and the last thing to
   suspect, not the first.

## Contributing a port

If you get a second device to step 3, open an issue with:

- the device, SoC, RIL type and transport,
- the state table from step 3 with the first failing step,
- redacted log excerpts (`tools/redact-log.py`) showing the failure.

A trace that *contradicts* the M52 findings is as valuable as one that
confirms them.
