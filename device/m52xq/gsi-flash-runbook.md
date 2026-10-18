<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# GSI runbook: this device, via Odin on Windows

Written for the M52. The point of this file is the two rules that keep
the phone recoverable, and the one trap that costs people a day.

## What you need

| File | What it is |
|---|---|
| GSI AP package (`AP_gsi.tar` style) | Odin AP package containing the GSI `system.img` plus a `vbmeta.img` with verification disabled. Writes **system and vbmeta only**. |
| Stock boot AP package | Rollback insurance: a boot-only restore of the Magisk-boot state. |

Keep the full stock firmware set as well, including whatever base the
ROM's installer expects (Android 13 firmware for the official
LineageOS install on this device).

## Before you flash

1. **Copy your data off the phone.** Installing a GSI formats `/data`,
   and going back to the stock-derived ROM formats it again. No path
   preserves it.
2. Charge above 60%, and use the cable and port that worked for the
   bootloader unlock or the previous flash.
3. Confirm your EFS/persist backups exist and are readable. Do this
   before, not after.

## The flash

1. Phone off → **VolUp + VolDown, plug USB, release, then VolUp** →
   download mode. It should report `UNLOCKED`.
2. Odin: **AP slot only**. Leave BL, CP, CSC and Userdata empty. Auto
   Reboot on, Repartition off.
3. Start it and do not touch the cable until it finishes.
4. First boot may fail because the GSI cannot read the existing
   encrypted `/data`. Boot recovery, **format data**, and reboot.
5. Set up the GSI: skip accounts, connect Wi-Fi only, and get to adb.

## Rollback, any time

1. Download mode again.
2. Odin AP = the stock boot package, **or** reinstall the full ROM zip
   through its own recovery for the complete base.
3. Format data again on first boot: same encryption rule.

## Rules

- **Never flash BL, CP or CSC slots.** Only AP. The modem and bootloader
  partitions are the parts you cannot rebuild from the internet.
- No repartition.
- If a Linux-based flashing tool fails on your machine, stop. Do not
  keep retrying it; the proven path is what is written above.
- Take an EFS/persist backup before the first flash, and verify it
  actually restores before you rely on it.

## Working on a DSU-installed GSI

If the GSI is installed as a DSU, a normal reboot returns the phone to
the other installed system. Plan your work around framework restarts
rather than reboots, or install the GSI properly first. Otherwise a
reboot in the middle of an experiment silently moves you to the other
system, and every "the change had no effect" result becomes suspect.
