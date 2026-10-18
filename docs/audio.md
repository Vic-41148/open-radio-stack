<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Call audio on SM7325

Short page, because on this platform audio turned out **not** to be
the blocker that it is on some Samsung designs.

## What the vendor audio HAL does

- `adev_set_mode` honours the mode the framework requests. There is no
  forced `MODE_IN_CALL` on this platform, which is the failure mode
  seen on some Exynos designs.
- `MODE_IN_CALL` (mode 2) sets flag `0x20000` and stops FM if it is
  running.
- `IN_COMMUNICATION` routes through `voice_start_call`, i.e. the same
  path as a plain voice call rather than a separate IMS-specific path.

Net effect: the HAL does not need to be taught about IMS. It needs a
correct call to be placed on the modem voice path, which is what
happens once the IMS call setup reaches the media stage.

## What actually worked

On the GSI with the open IMS app, calls carried two-way audio with no
audio-side changes at all:

- MO call: `AMR-NB 12.2k`, both directions.
- MT call: `AMR-WB` at 16 kHz, both directions.

There was one practical timing detail worth knowing for MT calls: the
app delays microphone activation briefly after the ACK on an incoming
call, and without it the first audio can be clipped or one-way.

## Still open on the audio side

- No systematic test of codec negotiation beyond AMR-NB/AMR-WB.
- No test of in-call audio changes (Bluetooth, speaker, second call).
- ViLTE has no audio path at all, because there is no ViLTE.

If you are porting to another device, treat audio as a separate
hypothesis: verify the HAL honours `adev_set_mode`, then verify the
call reaches the voice path, and only then look at the IMS app.
