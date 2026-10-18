#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Vic-41148
# SPDX-License-Identifier: MIT
# Read-only inventory of a Samsung phone's radio stack.
#
# Collects the facts the docs ask you to establish first: who provides
# telephony, which RIL is present, which transport, which HALs are
# declared. It writes nothing to the device.
#
# WARNING: the output can contain identifiers (serial, IMEI, IPs,
# subscriber addresses). Run it through tools/redact-log.py before you
# share the output:
#
#   tools/collect-device-info.sh > inventory.txt
#   tools/redact-log.py inventory.txt -o inventory-redacted.txt
#
set -uo pipefail

say() { printf '\n=== %s\n' "$*"; }

need_adb=1
command -v adb >/dev/null 2>&1 || {
  echo "adb not found in PATH" >&2
  exit 1
}
adb get-state >/dev/null 2>&1 || {
  echo "no device / unauthorized" >&2
  exit 1
}

say "device identity"
for p in ro.product.model ro.product.device ro.product.board ro.board.platform \
         ro.boot.bootloader ro.boot.hardware ro.build.version.release \
         gsm.version.baseband gsm.version.ril-impl \
         ro.telephony.default_network ro.vendor.radio.hal; do
  printf '%-34s %s\n' "$p" "$(adb shell getprop "$p" 2>/dev/null | tr -d '\r')"
done

say "radio / ims / telephony props"
adb shell getprop 2>/dev/null | tr -d '\r' \
  | grep -iE 'ril|radio|ims|telephony|carrier|qrtr|qmi' || true

say "telephony services (service list)"
adb shell service list 2>/dev/null | tr -d '\r' \
  | grep -iE 'radio|ims|telephony' || true

say "vendor HAL binaries"
adb shell 'ls /vendor/bin/hw 2>/dev/null' | tr -d '\r' \
  | grep -iE 'ril|radio|ims|qcril|qti|sec|samsung' || true

say "vintf manifest: radio / ims entries"
adb shell 'cat /vendor/etc/vintf/manifest.xml /vendor/etc/vintf/manifest/*.xml 2>/dev/null' \
  | tr -d '\r' | grep -iE -B2 -A6 'radio|ims' || true

say "init scripts (radio / ims / qti / sec)"
adb shell 'ls /vendor/etc/init /vendor/etc/init/hw 2>/dev/null' | tr -d '\r' \
  | grep -iE 'ril|radio|ims|qti|sec' || true

say "lshal (may need root: adb root)"
adb shell lshal 2>/dev/null | tr -d '\r' \
  | grep -iE 'radio|ims|qti|samsung' || true

say "transport processes"
adb shell 'ps -A 2>/dev/null' | tr -d '\r' \
  | grep -iE 'qrtr|qmux|rild|imsd|secims|ril|qti' || true

say "QRTR / QMI kernel modules"
adb shell 'ls /sys/module 2>/dev/null' | tr -d '\r' \
  | grep -iE 'qrtr|qmi|rmnet|ipa' || true

say "done"
echo "Redact before sharing: tools/redact-log.py <this output>"
