<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# CarrierConfig: the "no VoLTE option at all" failure

This was the actual root cause of the first failure on this device. It
is worth checking before touching anything else, because it looks like
a missing stack and is really one flag.

## The symptom

No VoLTE or VoWiFi option anywhere, voice falls back to circuit
switched. Calls still work, which makes it look like a working phone
with a missing feature.

## The cause

The CarrierConfig applied to the carrier on that ROM had:

```
carrier_volte_available_bool   = false
carrier_volte_provisioned_bool = false
carrier_wfc_ims_available_bool = false
vonr_enabled_bool              = false
```

With `carrier_volte_available_bool = false` the framework reports the
MMTEL feature as unavailable, so no VoLTE registration is ever
attempted and voice uses CSFB. `carrier_wfc_ims_available_bool` does
the same to VoWiFi, `vonr_enabled_bool` to 5G voice.

The stack underneath was fine the whole time: a complete vendor IMS
stack was present and the IMS data plane worked (IMS APN up, P-CSCF
discovered from the network).

## Check it on any ROM

`dumpsys` output varies by version; look for the four keys above and
their values for your carrier:

```sh
adb shell dumpsys carrier_config | grep -iE 'volte_available|wfc_ims_available|vonr_enabled'
```

On a Samsung stock ROM you can also see the vendor equivalent: the CSC
/ OMC decides IMS enablement there. Inspecting the CSC overlays on this
device showed the IMS stanza is shared across carriers and carries no
Airtel-specific IMS configuration, so this is not the layer that
differs per carrier.

## Fixing it

You are changing a config value, not patching a binary. Two routes:

1. An RRO overlay for the carrier, setting the values true. Sketch:

```xml
<resources>
  <bool name="carrier_volte_available_bool">true</bool>
  <bool name="carrier_volte_provisioned_bool">true</bool>
</overlay>
```

2. A carrier config XML for the MCC/MNC in question, loaded in place of
   the bad one.

Then confirm the framework actually picked it up: the values must
change in `dumpsys` and the MMTEL feature must become available. If
`dumpsys` still shows `false`, you have an overlay priority problem,
not a stack problem.

## Traps

- **An overlay that sets IMS values for one carrier can break another.**
  Set the values with the narrowest possible scope (carrier-specific
  overlay, not a global one).
- **Do not "fix" this by shipping a profile file that overwrites what
  the vendor profile already handles.** On this device the carrier
  profile was already correct; the profiles that broke registration
  were the hand-made ones. See `../../docs/carrier-config.md`.
- Flags and the stack are independent. Setting these true does **not**
  give you IMS if no ImsService is present, and having an ImsService
  does **not** help if these are false. Check both.
