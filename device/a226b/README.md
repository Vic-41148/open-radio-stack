<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# device/a226b: Galaxy A22 5G (MediaTek MT6833)

**Status: not worked on in this repo.** This page exists so the
counterpart case is on record, and because it is the reason the M52
result was surprising.

## What is known from that device

From earlier work on an A22 5G (MediaTek MT6833), which is a different
modem family and a different problem:

- Samsung's IMS service bridge can be made to run on an AOSP ROM, but
  the **`SETUP_DATA_CALL` for the IMS APN is rejected immediately**
  (with a `NAS_SIGNALLING`-class failure).
- The vendor RIL appears to look up an existing data-call object, find
  none, and reject in roughly 4 ms. The IMS PDN on that platform seems
  to expect a modem-native attach rather than a framework-requested
  data call.
- Activating the IMS PDN manually on a modem tty (`AT+CGACT`) does
  bring it up, but the RIL never learns about it, so the framework
  remains unaware.

These are recorded as prior observations, **not verified in this
repo**. Treat them as hypotheses to re-test if you work on the device.

## Why it matters here

On the M52 the same class of failure did not occur: the vendor RIL
accepted the IMS-APN data call on the first request. That is the single
biggest difference between the two devices, and it is why the M52 got
to a working call quickly.

If the A22 behaves as described, the interesting question is not SIP,
it is the data-call path: how that RIL decides to accept or reject a
framework-requested IMS bearer, and whether a modem-native attach can
be reconciled with what the framework expects.

## What a port would need

The same sequence as `../../docs/porting-guide.md`, with step 2
expected to fail: establish the stock baseline, then check the
transport and the IMS data-call path before building anything.

## Note on prior art

Community work on MediaTek Samsung IMS exists in the form of
bridge/patched-service approaches for other devices. Use those as
starting points rather than re-deriving the layout: the useful thing
this repo adds is the M52's contrasting result.
