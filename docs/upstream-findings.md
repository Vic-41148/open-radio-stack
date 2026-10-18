<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# Defects found in the open IMS apps

Found while bringing the open stack up on the M52. Ordered by how
much they matter. One is fixed and filed; the rest are written up so
whoever picks them up does not have to re-derive them.

Base for all of this: `krazey/ims` at `a3fec01`, with
`phhusson/ims` (`c180bdf`) as the ancestor. The code paths below are
inherited from phhusson unless stated.

## 1. Inbound SMS is never acknowledged: RP-ACK carries the wrong reference

**Severity: high. This silently breaks MT SMS completely on a network
whose SMSC validates the reference. Fixed and filed as
[krazey/ims#1](https://github.com/krazey/ims/pull/1).**

Inbound SMS arrives as an `RP-DATA` with a per-message reference:

```
01          RP-DATA from network
A4          RP-Message-Reference          <- unique per message
07 <oa>     originating address
00          destination address length
21 <tpdu>   TP-FO, OA, PID, DCS, SCTS, UDL, UD
```

The decoder reads that reference correctly, but the handler stores
only `(dest, callId, cseq)` with the pending ack. The ack is built
later from the `messageRef` the framework passes to
`acknowledgeSms()`: an internal tracker id, which was always `0`.

So the phone told the SMSC "I received message reference 0", which it
never sent. The SMSC answered:

```
05 00 01 51      RP-ERROR from network, RP-Message-Reference 0x00
```

`0x00` is an echo of our own ack, which is the tell. The message is
never marked received, so it is retransmitted on a fixed timer, and
**every message the SMSC sends afterwards queues behind that retry**:
the symptom is not "one lost SMS", it is "no MT SMS at all".

Controlled A/B, only the reference changed:

| ack reference | ack body (RP-MR `0xA4`) | network reply | outcome |
|---|---|---|---|
| framework tracker (`0`) | `02 00 41 02 00 00` | `05 00 01 51` | RP-ERROR, retry every ~5 min |
| RP-DATA reference (`0xA4`) | `02 A4 41 02 00 00` | *(none)* | accepted, message complete |

The trailing `41 02 00 00` ("empty delivery report") is **not**
implicated: it was present in the accepted ack too. The reference byte
is the whole story.

**Fix**: keep the decoded reference with the pending ack and echo it.
Two files, and the existing comment on the decode
(`// ref needs to be used in ACK`) finally becomes true:

```
SmscAddress.kt      smsHeaders gains:  val rpRef: Byte = 0
SipSmsHandler.kt    smsHeadersMap[nextToken] = smsHeaders(dest, callId, cseq, sms.ref)
                    val ackRef = headers.rpRef.toInt() and 0xff   // was: ref
```

**Effect, measured:** fifteen minutes of queued messages (seven stuck
ones) were delivered within about two seconds of the first correct
ack, and normal MT SMS has worked since with no settings and no
RP-ERRORs.

**To apply it:** `patches/0001-sms-ack-rp-reference.patch` carries the
same change as a commit, so `git am` into a `krazey/ims` checkout
keeps the message and the authorship. See `patches/README.md`.

Why it hid for so long: a plain "did an SMS arrive?" test passes. The
early IMS test checked that a MESSAGE arrived and was answered
`200 OK`, which it was. Only the *RP-level* ack was wrong, and the
consequence (a stalled queue) looks like a carrier problem.

`phhusson/ims` has the same code, in one file (`SipHandler.kt`, which
defines `smsHeaders` and builds the ack). The fix applies verbatim
there.

## 2. `main` does not compile with its own checked-in `app/libs/android.jar`

**Severity: high for anyone building it.** Eight errors: six
`isNetworkRegistered`, a three-argument `notifyIncomingCall`, an
ambiguous `setListener`. The shipped jar is stale relative to the
source.

Workaround, verified: build against a current full AOSP API-34
`android.jar` and pass it explicitly, e.g.
`-PplatformApiJar=/path/to/aosp-android-34.jar`. The vendored jar is
also mentioned in the project README as something you may need to
adjust, so this may be a known wart, but as shipped, `main` cannot be
built unattended.

## 3. Legacy fallback hands the framework a fabricated status report

**Severity: low (defence in depth).** `SipSmsHandler.kt`: the normal
path completes the outgoing SMS from the RP result, but if
`completePendingOutgoingSms()` returns `false` the fallback still fires
`onSmsStatusReportReceived(smsRefToInt(request), "3gpp", ByteArray(2))`,
i.e. a made-up two-byte report. A three-line change; an issue rather
than an argument.

## 4. A fresh random From/To tag per message when the caller supplies none

**Severity: low (latent).** `SipMessage.kt` mints a new random tag per
message (via-branch too) unless told otherwise. In practice the dialog
header builder sets tags explicitly for dialog traffic, so this is a
footgun rather than a live bug: report it as hardening.

## 5. Two items worth re-verifying before filing

Both date from the phhusson tree and krazey's `handleUpdate` has since
been rewritten, so check each against current `main` first:

- No IMS media session appears to be opened in some paths.
- `handleUpdate()` appears to send `180 Ringing` after its own `200 OK`.

## What to send where

- **`phhusson/ims`:** one thing only: the one-character compile fix
  (an unbalanced `(` that breaks the build). It is the only change that
  unblocks every downstream fork.
- **`krazey/ims`:** item 1 as a PR (filed), items 2 to 4 wherever the
  project will take them. Its issue tracker is disabled and it has no
  discussions, so that means a comment on the PR or a post where the
  project is discussed. Tiny, concrete, verifiable.
- Anything substantial later should be rebased onto krazey `main`
  first, so it is not re-fixing what krazey already fixed.
