<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# patches/

Drop-in fixes for the open IMS apps this repo reports on. They live in
their own directory on purpose: the code they change is `GPL-2.0-only`,
which does not combine with the `MIT` scripts or the `CC-BY-4.0` prose
here. Never merge a patch body into the rest of the tree, and never
copy source from the projects it targets (`NOTICES.md`).

| Patch | Target | Base commit | Status |
|---|---|---|---|
| [`0001-sms-ack-rp-reference.patch`](0001-sms-ack-rp-reference.patch) | `krazey/ims` | `a3fec01` | Filed and open: [krazey/ims#1](https://github.com/krazey/ims/pull/1) |

## 0001: ack incoming SMS with the RP reference from the RP-DATA

The IMS app decodes the RP-Message-Reference of an incoming SMS, drops
it, and then builds the RP-ACK from the framework tracker id, which is
always `0`. A network whose SMSC validates that reference answers
RP-ERROR, the message is never acknowledged, and every message the
SMSC sends afterwards queues behind the retry, so no MT SMS arrives at
all. The full analysis and the A/B evidence are in
`docs/upstream-findings.md` item 1.

Apply it to a `krazey/ims` checkout:

```sh
git clone https://github.com/krazey/ims
cd ims
git am /path/to/0001-sms-ack-rp-reference.patch
```

`git am` keeps the commit message and the authorship. If `main` has
moved and the context no longer matches, reduce the context instead:

```sh
git apply --3way 0001-sms-ack-rp-reference.patch
git apply -C1    0001-sms-ack-rp-reference.patch
```

On `phhusson/ims` the change is the same three lines, but the file
layout differs: that tree keeps `smsHeaders` and the ack builder
together in `SipHandler.kt`, so this patch file will not apply
verbatim. Make the change by hand there.

## Licence

`0001-sms-ack-rp-reference.patch` patches `GPL-2.0-only` code and is
`GPL-2.0-only` itself: the SPDX tag is in the `.license` sidecar and
the full text is `LICENSES/GPL-2.0-only.txt`. This README, like the
rest of the prose here, is `CC-BY-4.0`.
