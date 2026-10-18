#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Vic-41148
# SPDX-License-Identifier: MIT
# Confirm how the RIL talks to the modem on Samsung Qualcomm devices.
#
# The modern case (SM7325 era) is QMI over QRTR/MHI: no qmuxd daemon
# anywhere, QCRIL stubbed out. This script checks that positively and
# negatively so you know which tooling applies to your device.
#
# Read-only. Exit status 0 = QRTR transport detected.
set -uo pipefail

command -v adb >/dev/null 2>&1 || { echo "adb not found" >&2; exit 2; }
adb get-state >/dev/null 2>&1 || { echo "no device / unauthorized" >&2; exit 2; }

hit() { printf '  %-5s %s\n' "$1" "$2"; }
qrtr_found=0

echo "kernel modules"
for m in qrtr qrtr-mhi qrtr-smd qrtr-haven; do
  if adb shell "ls -d /sys/module/$m" >/dev/null 2>&1; then
    hit "yes" "$m"; qrtr_found=1
  else
    hit "no" "$m"
  fi
done

echo "processes"
for p in qrtr-ns qmuxd rild; do
  line=$(adb shell "ps -A 2>/dev/null" | tr -d '\r' | grep -i "[${p:0:1}]${p:1}" || true)
  if [ -n "$line" ]; then
    hit "yes" "$p  ->  $(echo "$line" | head -1 | awk '{print $NF}')"
    case "$p" in qrtr-ns) qrtr_found=1 ;; esac
  else
    hit "no" "$p"
  fi
done

echo "libraries and sockets"
for f in /vendor/lib64/libqrtr.so /vendor/lib64/libqrtrclient.so; do
  adb shell "ls $f" >/dev/null 2>&1 && hit "yes" "$f" || hit "no" "$f"
done
for f in /vendor/lib64/libqmi_client_qmux.so /vendor/bin/qmuxd; do
  adb shell "ls $f" >/dev/null 2>&1 && hit "present" "$f" || hit "absent" "$f"
done

echo "QRTR sockets"
adb shell 'ls /dev/socket 2>/dev/null; ls /dev/qrtr* /dev/mhi* 2>/dev/null' \
  | tr -d '\r' | grep -iE 'qrtr|mhi|qmi' || echo "  (none listed)"

echo
if [ "$qrtr_found" = 1 ]; then
  echo "RESULT: QMI over QRTR/MHI is present. Expect no qmuxd, and libsec-ril"
  echo "        or QCRIL speaking QMI directly on qrtr sockets."
  exit 0
else
  echo "RESULT: no QRTR detected. Look for legacy qmux sockets or an AT tty"
  echo "        instead, and adjust your tooling (different toolchain, and"
  echo "        the data-call path in docs/ims-pdn.md may not match)."
  exit 1
fi
