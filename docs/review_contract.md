# Review page contract (v0.2) — for Ana

The review page (Quarantine v2) is where a person sees what Shyft proposes and says yes,
change, or not now. This file fixes the **shapes** the page reads and writes, so the page
and the agent can be built at the same time. How the files travel (a small local server
vs. a downloaded file) is decided in S10; the shapes below do not change with it.

Status words: **fixed** = build against it. **proposed** = team decision pending; the
page must work with the field missing.

Each screenshot carries two separate answers (team decision D24):
- **handling**: did Zippy lock it, and as which kind? (`state`, `kind`)
- **disposition**: what should happen to the file? (`action`)

Never mix them: "locked" is never an action.

## 1. What the page reads: `review.json` (fixed)

Written by our code after a run, from `trace.jsonl`. The page never reads the trace
itself and never reads screenshots outside the list below.

```json
{
  "contract": "0.2",
  "run_id": "20261114-133641",
  "made": "2026-11-14T13:52:10",
  "counts": {"total": 91, "open": 61, "locked": 25, "copies": 5},
  "items": [
    {
      "id": "f3a91c0e5b7d2e48",
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
      "id": "9b04e7d1a2c65f30",
      "file": "Screenshot (77).png",
      "file_date": "2016-03-04",
      "state": "locked",
      "kind": "bank_or_payment",
      "action": null,
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
| `id` | An opaque string written by our code. **Same file in the same place = same id in every run.** The page stores and sends it back; it never builds, parses or shows it. |
| `state` | `open` (Pip proposed), `locked` (Zippy stopped it), `copy` (exact copy of an older file) |
| `kind` | Zippy's answer. One of: `none`, the 9 kinds in section 3, or `gate_error` (Zippy's answer was broken, so we locked it to be safe). Always `none` for `open` items. The only thing known about a locked file. |
| `action` | The proposed disposition: `keep_image`, `keep_text`, or `to_be_deleted`. **`null` for locked items**: nobody has proposed what to do with them yet. `copy` items are `to_be_deleted`. |
| `new_name` | suggested name without extension, or `null` (no rename needed, or locked) |
| `reason`, `why_saved` | Pip's words. **Always `null` for locked items.** `why_saved` is a guess: say so on screen. |
| `confidence` | 0 to 1, or `null`. Zippy's for locked items, Pip's for open ones. Not shown as a number to users (see rules). |
| `needs_ok` | true = Bloop's pile: locked, flagged unsure, or broken. Show these first or apart. |
| `copy_of` | for `state: copy`, the older file's name |
| `file_date` | the file's own date; the later age rule ("probably done its job") uses it |

## 2. What the page writes: `decisions.json` (fixed)

One entry per item the person decided, matched by `id`. Items without an entry are
**not decided** and appear again in the next `review.json`, with the same `id`.
Nothing moves until a separate step reads this file (execute).

```json
{
  "contract": "0.2",
  "run_id": "20261114-133641",
  "decisions": [
    {"id": "f3a91c0e5b7d2e48", "decision": "approve",
     "action": "keep_text", "new_name": "lisbon-flight-confirmation",
     "time": "2026-11-15T09:12:44"},
    {"id": "9b04e7d1a2c65f30", "decision": "change",
     "action": "to_be_deleted", "new_name": null, "time": "2026-11-15T09:13:02"}
  ]
}
```

- `decision`: `approve` (as proposed), `change` (the person picked another action and/or
  typed another name), `skip` (not now; same as no entry, but recorded).
- `action` / `new_name`: what should actually happen, after any change.
- **Locked items:** there is nothing to approve. The person may choose `keep_image`
  (leave it as it is) or `to_be_deleted` (move it to the folder), or skip. Never offer
  `keep_text` for a locked item: it would mean reading its text.
- Names the person types: the page may send them as typed; our code cleans them.

## 3. Zippy's kinds and the words a person sees (fixed kinds, copy is Raaghavi's)

Nine kinds, in ladder order, most harmful to expose first (D23):
`nudity_or_children` · `government_id` · `credentials` · `health_record` ·
`bank_or_payment` · `official_document` · `private_message` · `contact_details` ·
`marked_confidential`. Plus `gate_error` (shown with the locked items, at the end).
The page may sort or group locked items by this order.
Each of these 10 values gets one line of copy written by people, e.g. "Looks like a bank
or payment record. I stopped reading it." The model never writes a sentence a user sees.

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

## Changes from v0.1

1. `kind`: 9 kinds, not 8, and `gate_error` is listed as a value.
2. `action` is `null` for locked items (was `"sensitive"`), so handling and disposition
   stay separate. Locked items can be kept or moved, never `keep_text`.
3. `id` no longer contains the run id. It stays the same across runs, so a skipped item
   keeps its id and a decision still matches it next time.
