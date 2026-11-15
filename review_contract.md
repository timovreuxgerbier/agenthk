# Review page contract (v0.1, S9 draft) — for Ana

The review page (Quarantine v2) is where a person sees what Shyft proposes and says yes,
change, or not now. This file fixes the **shapes** the page reads and writes, so the page
and the agent can be built at the same time. How the files travel (a small local server
vs. a downloaded file) is decided in S10; the shapes below do not change with it.

Status words: **fixed** = build against it. **proposed** = team decision pending; the
page must work with the field missing.

## 1. What the page reads: `review.json` (fixed)

Written by our code after a run, from `trace.jsonl`. The page never reads the trace
itself and never reads screenshots outside the list below.

```json
{
  "contract": "0.1",
  "run_id": "20261114-133641",
  "made": "2026-11-14T13:52:10",
  "counts": {"total": 91, "open": 61, "locked": 25, "copies": 5},
  "items": [
    {
      "id": "20261114-133641:Screenshot (41).png",
      "file": "Screenshot (41).png",
      "file_date": "2026-10-29",
      "state": "open",
      "kind": "none",
      "action": "keep_text",
      "new_name": "lisbon-flight-confirmation",
      "reason": "A flight confirmation with dates and a booking reference.",
      "why_saved": "Probably kept to check travel times (a guess).",
      "confidence": 0.95,
      "needs_ok": false,
      "copy_of": null
    },
    {
      "id": "20261114-133641:Screenshot (77).png",
      "file": "Screenshot (77).png",
      "file_date": "2016-03-04",
      "state": "locked",
      "kind": "bank_or_payment",
      "action": "sensitive",
      "new_name": null,
      "reason": null,
      "why_saved": null,
      "confidence": 0.99,
      "needs_ok": true,
      "copy_of": null
    }
  ]
}
```

| field | meaning |
|---|---|
| `state` | `open` (Pip proposed), `locked` (Zippy stopped it), `copy` (exact copy of an older file) |
| `kind` | Zippy's answer: `none` or one of the 8 kinds below. The only thing known about a locked file. |
| `action` | `keep_image`, `keep_text`, `to_be_deleted`, or `sensitive` (= locked) |
| `new_name` | suggested name without extension, or `null` (no rename needed, or locked) |
| `reason`, `why_saved` | Pip's words. **Always `null` for locked items.** `why_saved` is a guess: say so on screen. |
| `confidence` | 0 to 1, or `null`. Not shown as a number to users (see rules). |
| `needs_ok` | true = Bloop's pile: locked, flagged unsure, or broken. Show these first or apart. |
| `copy_of` | for `state: copy`, the older file's name |
| `file_date` | the file's own date; the later age rule ("probably done its job") uses it |

## 2. What the page writes: `decisions.json` (fixed)

One entry per item the person decided. Items without an entry are **not decided** and
appear again next time. Nothing moves until a separate step reads this file (execute).

```json
{
  "contract": "0.1",
  "run_id": "20261114-133641",
  "decisions": [
    {"id": "20261114-133641:Screenshot (41).png", "decision": "approve",
     "action": "keep_text", "new_name": "lisbon-flight-confirmation",
     "time": "2026-11-15T09:12:44"},
    {"id": "20261114-133641:Screenshot (77).png", "decision": "change",
     "action": "to_be_deleted", "new_name": null, "time": "2026-11-15T09:13:02"}
  ]
}
```

- `decision`: `approve` (as proposed), `change` (the person picked another action and/or
  typed another name), `skip` (not now; same as no entry, but recorded).
- `action` / `new_name`: what should actually happen, after any change.
- Names the person types: the page may send them as typed; our code cleans them.

## 3. Zippy's kinds and the words a person sees (fixed kinds, copy is Raaghavi's)

In ladder order, most harmful to expose first (D23): `nudity_or_children` ·
`government_id` · `credentials` · `health_record` · `bank_or_payment` ·
`official_document` · `private_message` · `contact_details` · `marked_confidential` ·
plus `gate_error` (Zippy's answer was broken, so we locked it to be safe).
The page may sort or group locked items by this order.
Each kind gets one line of copy written by people, e.g. "Looks like a bank or payment
record. I stopped reading it." The model never writes a sentence a user sees.

## 4. Page rules that come from the architecture (fixed)

1. A locked item shows its kind's copy, its date and nothing else by default. **No
   thumbnail.** Showing the image is a deliberate click ("show me"), never on hover.
2. Never show Pip's text for a locked item (it is `null` anyway; don't invent any).
3. Nothing is deleted. `to_be_deleted` means "moved to the To Be Deleted folder".
   No red destructive buttons; the copy never says "delete 3".
4. One item per screen is the default; progress always visible ("4 of 91"); "stop here"
   always visible and loses nothing; no timers; keyboard-only works; reduced motion;
   colour is never the only signal (each buddy's meaning also in words).
5. Confidence is never shown as a number. `needs_ok` decides what asks for attention.

## 5. Proposed, not decided (the page must work without them)

- `locked_name` (string or null): a name **our code** writes from kind + file date,
  e.g. `bank-or-payment-2016-03`. Gives locked files a name without anyone reading
  them. Changes what "locked" promises ("untouched" → "named by kind only"), so it goes
  to the team first. Off by default.
- A "probably done its job" group: old file + a kind that expires (age rule, not built).
