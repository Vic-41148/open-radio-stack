<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# device/m52xq: Samsung Galaxy M52 5G

| | |
|---|---|
| Model | SM-M526B/DS |
| Codename | `m52xq` (this unit reports the ported-ROM identity `r0q` when a One UI port is installed) |
| SoC | SM7325 / Snapdragon 778G |
| Modem | Qualcomm, baseband family `kodiak` |
| Reference SIM | Airtel India (MCC/MNC 404/10) |

## Which base you are on matters

| Base | Radio stack | IMS |
|---|---|---|
| Stock Samsung (Android 13) | Samsung `rild` + `libsec-ril` + Samsung `imsservice` + CSC/OMC | Works. This is the reference. |
| One UI port, e.g. UN1CA | Same Samsung stack, carried over | Works, for the same reason: the vendor stack comes with it. |
| LineageOS (official tree, Simon1511) | AOSP radio HAL on the vendor RIL | No IMS service is available in-tree; see the note below. |
| LineageOS GSI (this work) | AOSP radio HAL on the vendor RIL | **Works with an open ImsService installed**, see `../../docs/open-ims-on-gsi.md`. |

Two practical notes:

- The official LineageOS install for this device expects a **stock
  Android 13 firmware base** first. Check the LineageOS wiki page for
  the device before you start.
- A GSI installed as a DSU is **single-shot** in the way it was set up
  here: a normal reboot returns the phone to the other system. That
  constrains how you work: plan for framework restarts instead of
  reboots, or install the GSI properly.

## Verified on this device

- Vendor transport: `rild` + `libsec-ril` over QMI/QRTR-MHI, `qmuxd`
  absent, QCRIL stubbed. → `../../docs/architecture.md`
- The vendor RIL accepts the IMS-APN `SETUP_DATA_CALL` and delivers
  P-CSCF via PCO. → `../../docs/open-ims-on-gsi.md`
- VoLTE MO+MT, SMS MO+MT over IMS, DTMF, teardown, with an open
  ImsService on a LineageOS 21 GSI.
- The "no VoLTE option" failure on this device's ported ROM was a
  CarrierConfig flag, not a missing stack. → `carrierconfig.md`

## Other people's work you should use instead of redoing

- Device trees: `LineageOS/android_device_samsung_m52xq` and the shared
  `android_device_samsung_sm7325-common`.
- Kernel: `android_kernel_samsung_sm7325`.
- The LineageOS wiki page for `m52xq` lists the maintainer and the
  install requirements.

Nothing in this repo replaces those; this repo documents the radio
layer that sits underneath them.
