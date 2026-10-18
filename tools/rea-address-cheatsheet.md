<!--
SPDX-FileCopyrightText: 2026 Vic-41148
SPDX-License-Identifier: CC-BY-4.0
-->

# REA / Ghidra address cheatsheet (Samsung userspace libs)

Short, because it is a list of ways to be wrong.

## Addresses

- On these libraries, the address you read from `nm`/`dwarf` symbols is
  **not** the address in the analysis project. The relationship that
  held for the SM7325 libraries was:

  ```
  analysis address = load address + 0x100000
  ```

- **Verify it every session.** Print the function header line at your
  computed address and check it looks like a function prologue before
  trusting anything derived from it. A wrong address does not return an
  error; it silently returns a *different real function*, which is how
  bad findings get written down.
- Record the binary's hash next to every finding. `dump-ril-symbols.sh`
  prints it for you. An analysis is only valid for that exact build.

## Tooling behaviour

- **Serial runs only.** Parallel Ghidra provider calls on these
  binaries produced `provider_timeout` storms here. One at a time.
- Keep the decompiler's own naming; do not rename symbols to match your
  hypothesis until the hypothesis is proven.
- Save the raw decompiler output next to the claim. Paraphrase is not
  evidence.

## Cross-checking

Three independent views, in order of cost:

1. **Static**: the function body, with its callers.
2. **Strings and call sites**: log format strings usually name the
   failure path, which narrows a search enormously.
3. **Live**: the same code path on a rooted device, with the log line
   that proves it ran.

If a claim only has view 1, mark it as an inference, not a fact. The
sections in `../docs/` follow that rule.

## Library split on this platform

- Vendor RIL (`libsec-ril.so`): data-call truth, QMI message layout.
- Vendor IMS (`libsec-ims.so`): SIP, IPsec, DNS, SMS-over-IMS.
- Java glue (`com.sec.imsservice`): request shapes, profile selection.

Each is independently analysable from a single AP image pull, and each
answers a different class of question. Check which one your question
belongs to before opening a disassembler.
