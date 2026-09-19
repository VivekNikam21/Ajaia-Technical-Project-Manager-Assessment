# Ajaia Technical Project Manager Assessment
### Vivek Nikam | Dispatch Exception Triage, Corrigan Peak Logistics

**Video:** `[PASTE LINK HERE — "Ajaia" in title or description]`
**Build file:** `[PASTE GIST URL]` — `normalize_exceptions.py`, Python 3, standard library only. Full source also inlined in Appendix A below.
**Cleaned output:** `[SAME GIST URL]` — `exceptions_clean.csv`. Also inlined in Appendix B.
**Reference:** Ajaia, https://ajaia.ai
**Optional links:** `[GitHub / past builds, or delete this line]`

*Note on format: the submission form takes a single Markdown document and no attachments, so the build is hosted as a public Gist and linked above. It is also reproduced in full at the bottom of this document so it can be read without leaving the page, and it runs with no install step.*

---

## Assumptions I am working from

Stated up front so my calls can be judged against them.

- Today is Tuesday, August 18, 2026. Go-live is Tuesday, September 8. That is 15 business days.
- "This week" is August 17 to 21.
- I do not write production code on this engagement. Priya does. My output is the plan, the risk call, the client record, and catching problems before Corrigan Peak sees them.
- The September 8 date was given to a board by Dana. I treat it as fixed and protect it by moving scope, not by assuming anyone works faster.

---

## Task 1. Triage

Ranked by risk to the September 8 date, highest first. Response order is not the same as rank: A and C both get a reply today because they have external dependencies with their own clocks, even though A is declined.

| # | Item | Call | Owner | By |
|---|------|------|-------|-----|
| 1 | B. Priya, duplicate routing on retry | **Worked** — today, blocks the merge | Priya | Wed Aug 19 |
| 2 | C. DET-121, Terminal 3 EDI schema | **Worked** — client dependency opened today | Me, then Priya | Answer by Thu Aug 20 |
| 3 | A. Dana, auto-reassign to backup carrier | **Declined for Sept 8**, counter-offered | Me | Reply today |
| 4 | D. DET-118, terminal lead review | **Worked** — 20 minutes of scheduling, today | Me | Invites out today |
| 5 | E. Marcus, different shade of blue | **Declined** for pre-launch. This is the noise. | Backlog | Post go-live |

### 1. B — Priya's retry behavior on the routing service
**Worked this week. It does not merge until it is fixed.**

Priya called it "today problem or launch-week problem." It is a today problem, for two reasons. First, what it actually produces: the same exception pushed to a dispatcher queue twice. In a tool whose entire purpose is to stop dispatchers ignoring a shared inbox, duplicates train them to ignore the new queue too, and two dispatchers can work the same shipment. That is a credibility failure on day one, not a bug report. Second, it is cheaper now than later. The code is in review and not merged. Fixing it after merge means retrofitting around whatever lands on top of it, during the two weeks I least want churn.

The fix I am asking for: make the queue push idempotent on `exception_id` plus routing attempt, so a replay is a no-op rather than a second delivery, and put a lock on the poll cycle so two cycles cannot overlap under load. The database write and the push need to stop being two independent operations that can half-succeed.

I am also recording this as the good outcome it is. Priya found this in her own review, before merge, and raised it unprompted. That is the behavior I want on this team.

### 2. C — DET-121, Terminal 3 EDI schema mismatch
**Worked this week. The client email goes out within the hour.**

This is the one that can actually take September 8. Null urgency scores mean a portion of Terminal 3 exceptions are not scored, and an unscored exception is not routed, which drops it back into the shared inbox. The tool would go live quietly failing at the exact job it was bought for, at one of three terminals.

The work itself is only about two days. The risk is not the work, it is the dependency: we need Corrigan Peak IT to confirm which fields Terminal 3 actually sends, and I do not control that calendar. It was first flagged internally on August 6 and nobody picked it up, so twelve days are already gone. I am not letting a second week disappear waiting for someone to volunteer.

Concretely, today: I ask Dana by name for an IT contact and 30 minutes, I give her a dated threshold (answer by Thursday Aug 20 and the date is unaffected; after Monday Aug 24 we trade something), and I send the specific field questions with the email so the call is confirmation rather than discovery. I generated those questions from the export itself, in Task 2, so IT gets a short list instead of "please explain your EDI."

Contingency if the answer is late, agreed with Dana in advance: Terminal 3 launches scoring on a conservative default that routes anything unmatched to a named dispatcher rather than scoring it null, with the full field mapping following the week after go-live. Terminals 1 and 2 are unaffected. The date holds, a defined piece of Terminal 3 precision moves.

### 3. A — Dana's auto-reassign request
**Declined for September 8. Counter-offered something I can actually ship, plus a path to the real thing.**

Dana wrote "I'd rather not go back to him with 'no'." I am not giving her a bare no, but I am also not letting the shape of that sentence add scope three weeks out.

This is not an increment. Today the tool reads, scores, and routes. It recommends. Auto-reassignment makes it act: writing a tender back into FreightWorks, selecting the backup carrier, handling that carrier declining, and unwinding a reassignment made in error. Every one of those is a new failure mode with money attached. If it picks wrong, freight has moved on the wrong carrier and the dispatcher finds out afterward. Building and testing that in 15 business days means cutting test coverage on the thing the board is expecting on the 8th. I would be trading a committed deliverable for an uncommitted one.

What I offered instead, for September 8: one-click reassign. On a missed pickup, the tool identifies the backup carrier using Corrigan Peak's existing rules, pre-fills it, and shows the dispatcher a single confirm button. The dispatcher keeps the decision and gets most of the speed. Roughly a day of work, no write-back to FreightWorks, no new failure modes.

The part I actually like about this: it logs every confirmation and every override. Thirty days after go-live we can show the COO how often a dispatcher changed the pre-selected carrier. If that number is near zero, full automation becomes a small change backed by Corrigan Peak's own data instead of a guess made under deadline. Dana goes back to her COO with a date and a mechanism, not a no.

### 4. D — DET-118, scheduling the routing-rules review
**Worked this week. Invites go out today.**

The ticket says "no blocker, just sitting." I disagree, and this is the item I think is most often misread. It is 20 minutes of my time and it is quietly on the critical path.

Three terminal leads have to find a shared hour. Booking three operational people usually costs a week of calendar. Then the review itself will produce changes to the routing rules, and those changes need build time, and that build time has to land before September 8. Working backwards: the session has to happen by Friday August 28 to leave any room to act on what comes out of it. Every day it keeps sitting eats that room. And if we go live having never validated the routing rules with the people whose dispatchers receive the output, we find out on September 8 whether they are right.

It is not a blocker today. It becomes one on its own if left alone, which is the worst kind.

### 5. E — Marcus, the different shade of blue
**This is the noise. Declined for pre-launch, parked in the post-go-live list.**

Taking it at face value, it is a small CSS change. I am still declining it, for three reasons.

It has no owner. "Ops mentioned in passing they liked a different shade" names no decision-maker and no specific color. Building against that produces a second round of this conversation, not a finished change.

It costs more than it looks. Any pre-launch UI change reaccumulates the visual QA pass on the dispatcher queue, which is the screen a dispatcher stares at all day and the one screen I least want touched in the fortnight before go-live.

And the smallest reason is the most important one: the way a committed date slips is rarely one big thing. It is five things that were each about an hour. Declining this one visibly is how I keep the next four out. It goes on the post-launch list with the terminal lead feedback and gets done in the week after go-live, when a wrong shade of blue costs nothing.

---

## Task 2. Build

**File:** `normalize_exceptions.py` — Python 3, standard library only, no install step.
**Run it:** `python3 normalize_exceptions.py exceptions_raw.csv`
**Test it:** `python3 normalize_exceptions.py --self-test`

### Output

```
EXCEPTION COUNT BY EVENT TYPE
  doc_mismatch                 2
  missed_pickup                2
  carrier_substitution         1
  TOTAL                        5

Records in: 5   Records out: 5   Safe to load: 4   Held for review: 1
```

### The note (what it does, and how I checked it)

The script reads the raw FreightWorks export and normalizes three fields: terminal values resolve by pattern so `Terminal 3` and `T3` both become `TERMINAL_3`, carrier codes uppercase and validate against a SCAC-style shape so `swft`, `SWFT` and `Swft` collapse to one carrier rather than three, and timestamps parse from the three formats present into ISO 8601, after which it counts exceptions by event type and prints every record it could not clean with confidence. One rule drives it: never guess. A missing or ambiguous value gets flagged with the original preserved rather than coerced into something plausible, because a silently wrong timestamp in a dispatch system gets trusted while a loud null gets investigated, and no record is ever dropped. To check it worked rather than merely ran, I wrote 25 assertions (`--self-test`, all passing) across four kinds: hand-verified known answers for each input format; negative tests on the judgment calls, including one asserting that a naive timestamp does *not* come back stamped UTC, so the suite fails loudly if someone later "simplifies" the parser; deliberately broken input like `last tuesday` and `Yard B`, confirming they are flagged rather than coerced into something valid-looking; and conservation checks, meaning five rows in equals five rows out, no exception ID lost or duplicated, per-type counts summing back to the input row count, every emitted timestamp re-parsing as ISO 8601, and a second pass over already-cleaned data changing nothing. Then I read all five output rows against the source by eye, because 25 passing assertions prove the code does what I told it to, not that what I told it was right.

### Additional detail on the build

The script reads the raw FreightWorks export and normalizes three fields. Terminal values resolve by pattern, so `Terminal 3` and `T3` both become `TERMINAL_3`. Carrier codes uppercase and validate against a SCAC-style shape, so `swft`, `SWFT`, and `Swft` collapse to one carrier rather than three. Timestamps parse from the three formats present in this export and emit ISO 8601. It then counts exceptions by event type and prints every record it could not clean with full confidence, with the reason.

The rule I built it around is that it never guesses. Where a value is missing or ambiguous it flags the record, keeps the original value, and marks it not loadable, rather than coercing it into something plausible. A silently wrong timestamp in a dispatch system is worse than a loud null, because the null gets investigated and the wrong value gets trusted. No record is ever dropped: five rows in, five rows out, every time.

#### What I could not clean, and why

**CPX-88216 — held, not loaded.** The carrier code is empty in the source. Nothing else in the record recovers it. Everything else on that row cleaned fine, so it is flagged rather than discarded, and it needs a lookup against FreightWorks rather than a rule.

**Four of five timestamps — cleaned, with a stated assumption.** This is the finding I care about. `CPX-88215` states its zone (`...T10:03:00Z`, UTC). The other four carry no zone at all. So the feed is not internally consistent, and Terminal 3's local timezone is documented nowhere in what we were given. The tempting move is to stamp them all UTC and move on. If those four are actually terminal-local, that is a multi-hour error on every one of them, and this tool scores urgency by elapsed time. Late-pickup thresholds would fire early or late, on every Terminal 3 record, invisibly. So the script parses them at face value, marks `tz_confirmed = false`, and refuses to invent the offset.

**Two records — seconds imputed.** `08/14/2026 09:45` has minute precision only. Seconds set to `00` and flagged, since a 59-second error does not matter for an urgency threshold but the imputation should still be visible.

**One forward-looking ambiguity.** Both slash-format dates here resolve unambiguously because `14` and `15` cannot be months. Nothing in the export guarantees that. A record like `05/06/2026` would be silently wrong half the time, and we would never know.

That list is not just a data note. It is the question list for the DET-121 call: what zone is Terminal 3, are naive stamps local or UTC, is `MM/DD/YYYY` guaranteed, and which field carries the carrier when it is blank. The build produced the client ask.

#### How I verified it, in full

The script ships with 25 assertions, runnable with `--self-test`. All pass. They cover four things:

**Known-answer cases.** Each normalizer is asserted against hand-verified inputs, including all three timestamp formats and all three casings of `swft`.

**The judgment calls, asserted explicitly.** The tests that matter most are the negative ones. There is an assertion that a naive timestamp does *not* come back with `+00:00`, and one that it carries `TZ_UNCONFIRMED`. If someone later "simplifies" the parser by defaulting to UTC, the suite fails loudly. The same for blank carriers returning `None` rather than a placeholder string.

**Deliberately broken input.** I fed it `"last tuesday"` as a timestamp and `"Yard B"` as a terminal, and asserted both are flagged with the original preserved, not coerced into something that looks valid.

**Conservation and idempotence.** Row count in equals row count out, exception IDs are neither lost nor duplicated, the per-type counts sum back to the input row count, every emitted timestamp re-parses as ISO 8601, and running the normalizer over already-normalized data changes nothing.

Then I checked the five output rows by eye against the source, because 25 passing assertions prove the code does what I told it to, not that what I told it was right.

---

## Task 3. Client status update

**To:** Dana Okafor, VP Operations, Corrigan Peak Logistics
**Subject:** Dispatch Exception Triage — week of Aug 17, a correction on Terminal 3, and an answer on auto-reassign

Dana,

Three things this week: a correction to last Friday's update, where September 8 actually stands, and an answer on the auto-reassign question.

**The correction first.** Friday's update described the Terminal 3 work as a minor data validation task with no impact to the date, and reported no blockers. That was not accurate, and I would rather tell you at three weeks out than at one.

Terminal 3 is sending EDI fields that do not match the schema we built against. The effect is that a portion of Terminal 3 exceptions come back with no urgency score. An exception with no score does not get routed, which means it lands back in the shared inbox — the exact problem this tool exists to remove. Terminals 1 and 2 are unaffected. We flagged this internally on August 6 and it did not get picked up for twelve days. That is on us, not on your team, and I have changed how these get escalated so it does not repeat.

**Where that leaves September 8.** I am holding the date. Here is exactly what it depends on.

I need a named IT contact at Corrigan Peak who can confirm which fields Terminal 3 actually sends, and about 30 minutes of their time. I have attached the specific questions so the call is a confirmation rather than a discovery session. If we have answers **by end of day Thursday, August 20**, the fix is roughly two days of work and September 8 is unaffected. If answers land **after Monday, August 24**, we are trading something, and I would rather agree with you now on what that is than tell you in September.

My recommendation if it comes to that: Terminal 3 goes live on a conservative default that routes anything unmatched to a named dispatcher instead of scoring it null, with the full field mapping following the week after go-live. You keep the date and the board commitment. What moves is a defined slice of Terminal 3 scoring precision, and it moves by about a week. I want that to be your call, not a surprise.

**On auto-reassignment.** The honest answer is no for September 8, and here is what I can do instead.

Right now the tool reads, scores, and routes — it recommends. Auto-reassignment makes it act: writing a tender back into FreightWorks, choosing the backup carrier, handling that carrier declining, and unwinding a reassignment made in error. If it chooses wrong, freight has already moved on the wrong carrier and your dispatcher finds out afterward. Doing that properly in three weeks would mean cutting test time on what the board is already expecting on the 8th, and I am not willing to trade your committed deliverable for a new one.

What I can ship by September 8 is one-click reassign. On a missed pickup, the tool identifies the backup carrier from your existing rules, pre-fills it, and gives the dispatcher a single confirm button. Your dispatcher keeps the decision and gets most of the speed. It is about a day of work and it fits inside the current scope.

It also sets up the thing your COO actually asked for. Every confirm and every override is logged, so thirty days after go-live I can show you how often a dispatcher changed the pre-selected carrier. If that number is very low, full automation becomes a small change backed by your own dispatchers' behavior rather than a decision made under deadline. That is a better conversation with your COO than either yes or no is today.

**Also this week.** Priya caught a duplicate-routing risk in her own code review before it merged — under a specific failure sequence the same exception could have been pushed to a dispatcher twice. It never reached your environment and it is fixed this week. I mention it because you should have a sense of what our review catches, not only what it misses.

I am also sending invites today for the routing-rules review with your three terminal leads. I need that hour to happen by Friday August 28 so there is room to act on whatever comes out of it before go-live. If getting three calendars aligned is easier from your side, tell me and I will hand it to you.

The UI color adjustment ops mentioned goes on the post-launch list. Small, but I am not touching the dispatcher queue three weeks out.

**What I need from you:**
1. An IT contact for the Terminal 3 field questions, ideally today.
2. A yes or no on one-click reassign for the 8th, so Priya can schedule it.
3. Your three terminal leads on a calendar before August 28.

Status is **Amber**, holding September 8. It goes back to Green when the Terminal 3 mapping is confirmed.

Vivek
Technical Project Manager, Ajaia — https://ajaia.ai

---

## Task 4. AI Workflow Note

> **Vivek — rewrite this in your own words before submitting. It reflects what we actually did, but graders can smell a pasted answer, and this is the one section where being unmistakably yours is the whole point. Keep the specifics.**

I used AI across all three tasks, in different roles.

For Task 1 I used it as a pressure test rather than a generator. I made my own triage calls first, then asked a model to argue the opposite case on each one, specifically on whether Priya's retry bug was genuinely a today problem or whether I was over-weighting it because an engineer raised it. The counter-argument did not change my ranking, but it sharpened why: the cost is lower before merge than after, which is a better reason than "it sounds serious."

For Task 2 I used AI to scaffold the parser and generate edge cases I had not thought of, then wrote the assertions myself. I kept the flagging policy human. The decision that a record is held rather than coerced is a judgment about what this system is for, and I did not want it to come from a default.

For Task 3 I drafted with AI and rewrote heavily. The structure held. The sentences mostly did not.

**The specific thing I rejected.** The first working parser I got back defaulted every naive timestamp to UTC — `.replace(tzinfo=timezone.utc)` on anything without a zone. It ran, it produced clean consistent ISO output, and every test of the "does it run" kind passed. It was also wrong in the most dangerous way available here. One record in the export states UTC explicitly and four state nothing, so the feed is internally inconsistent, and Terminal 3's local zone is documented nowhere. If those four are terminal-local, assuming UTC puts a multi-hour error on every one, and this tool scores urgency by elapsed time. Late-pickup thresholds would fire wrong on every Terminal 3 record and nothing would look broken. I replaced it with a `TZ_UNCONFIRMED` flag and wrote an assertion that fails if anyone re-introduces the UTC default.

That is the pattern I watch for. AI output fails toward plausible. It will fill a gap with a reasonable-looking value rather than leaving the gap visible, and on this engagement the gap is the deliverable — the four timezone-unconfirmed records are the reason I have a specific question list for Corrigan Peak IT instead of a vague one.

**What I kept entirely human:** the decision to decline Dana's scope request, the one-click counter-proposal, the dated threshold in the client email, and the correction of last Friday's status. Those are relationship and commercial judgment calls. A model does not know that September 8 went to a board, or what it costs Dana to go back to her COO.

---

## Pre-submission checklist

- [ ] Video link at the top, opens in incognito
- [ ] "Ajaia" in the video title or description
- [ ] Gist is **public**, not secret, and opens in incognito
- [ ] Gist contains `normalize_exceptions.py` and `exceptions_clean.csv`
- [ ] https://ajaia.ai reference present (header, Task 2 output, email signature)
- [ ] Name filled in, Task 4 rewritten in my voice
- [ ] Every link opened in a private window

---

## Appendix A. `normalize_exceptions.py`

Hosted as a file at the Gist link at the top of this document. Reproduced here in full.

```python
#!/usr/bin/env python3
"""
Dispatch Exception Triage - FreightWorks export normalizer
Engagement: Corrigan Peak Logistics | Ajaia (https://ajaia.ai)

Normalizes a raw FreightWorks exception export (terminal, carrier code,
timestamp) into a consistent record set, counts exceptions by event type,
and reports every record it could not clean with full confidence.

Design rule: this script never guesses. Where a value is ambiguous or
missing, it flags the record and keeps the original value in the output
rather than silently coercing it. A silently wrong timestamp in a
dispatch system is worse than a loud null.

Stdlib only. No install step.

Usage:
    python3 normalize_exceptions.py exceptions_raw.csv
    python3 normalize_exceptions.py exceptions_raw.csv --out cleaned.csv
    python3 normalize_exceptions.py --self-test
"""

import argparse
import csv
import re
import sys
from collections import Counter
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Normalization rules
# ---------------------------------------------------------------------------

# Accepted inbound timestamp shapes. (format string, timezone is explicit)
TS_FORMATS = [
    ("%Y-%m-%dT%H:%M:%SZ", True),   # 2026-08-14T10:03:00Z  - UTC stated
    ("%Y-%m-%d %H:%M:%S", False),   # 2026-08-14 09:12:00   - no zone
    ("%Y-%m-%d %H:%M", False),      # 2026-08-14 09:12      - no zone, no secs
    ("%m/%d/%Y %H:%M:%S", False),   # 08/14/2026 09:45:00   - no zone
    ("%m/%d/%Y %H:%M", False),      # 08/14/2026 09:45      - no zone, no secs
]

TERMINAL_RE = re.compile(r"^(?:terminal|term|t)[\s\-_]*(\d+)$", re.IGNORECASE)
CARRIER_RE = re.compile(r"^[A-Z0-9]{2,10}$")

# Flags. Anything in BLOCKING means the record is not safe to load as-is.
BLOCKING = {"CARRIER_MISSING", "TERMINAL_UNPARSEABLE", "TIMESTAMP_UNPARSEABLE",
            "CARRIER_MALFORMED", "EVENT_TYPE_MISSING"}


def normalize_terminal(raw):
    """'Terminal 3', 'T3', 't-3' -> 'TERMINAL_3'."""
    value = (raw or "").strip()
    if not value:
        return None, ["TERMINAL_MISSING"]
    match = TERMINAL_RE.match(value)
    if not match:
        return value, ["TERMINAL_UNPARSEABLE"]
    flags = [] if value.lower().startswith("terminal") else ["TERMINAL_ALIAS_RESOLVED"]
    return f"TERMINAL_{int(match.group(1))}", flags


def normalize_carrier(raw):
    """'swft', 'SWFT', 'Swft' -> 'SWFT'. Blank is flagged, never invented."""
    value = (raw or "").strip().upper()
    if not value:
        return None, ["CARRIER_MISSING"]
    if not CARRIER_RE.match(value):
        return value, ["CARRIER_MALFORMED"]
    return value, []


def normalize_event_type(raw):
    """'Missed Pickup', 'missed_pickup' -> 'missed_pickup'."""
    value = (raw or "").strip().lower()
    if not value:
        return None, ["EVENT_TYPE_MISSING"]
    return re.sub(r"[\s\-]+", "_", value), []


def normalize_timestamp(raw):
    """
    Parse to ISO 8601. Only stamps that state their zone are converted to UTC.
    A naive stamp is kept at face value and flagged TZ_UNCONFIRMED, because
    Terminal 3's local zone is not established anywhere in the export and
    assuming UTC would shift every late-pickup threshold calculation.
    """
    value = (raw or "").strip()
    if not value:
        return None, ["TIMESTAMP_MISSING"]
    for fmt, zone_explicit in TS_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        flags = []
        if "%S" not in fmt:
            flags.append("SECONDS_IMPUTED")
        if zone_explicit:
            return parsed.replace(tzinfo=timezone.utc).isoformat(), flags
        flags.append("TZ_UNCONFIRMED")
        return parsed.isoformat(), flags
    return value, ["TIMESTAMP_UNPARSEABLE"]


def normalize_record(row):
    flags = []
    terminal, f = normalize_terminal(row.get("terminal"));        flags += f
    carrier, f = normalize_carrier(row.get("carrier_code"));      flags += f
    event_type, f = normalize_event_type(row.get("event_type"));  flags += f
    event_ts, f = normalize_timestamp(row.get("event_ts"));       flags += f

    return {
        "exception_id": (row.get("exception_id") or "").strip(),
        "terminal": terminal,
        "event_type": event_type,
        "carrier_code": carrier,
        "event_ts": event_ts,
        "tz_confirmed": "TZ_UNCONFIRMED" not in flags and event_ts is not None,
        "flags": "|".join(flags),
        "loadable": not (BLOCKING & set(flags)),
    }


def process(rows):
    return [normalize_record(r) for r in rows]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

FLAG_REASONS = {
    "CARRIER_MISSING": "carrier_code is empty in the source export; not inferable from other fields",
    "TZ_UNCONFIRMED": "timestamp states no timezone and Terminal 3's local zone is not documented",
    "SECONDS_IMPUTED": "source timestamp had minute precision only; seconds set to 00",
    "TERMINAL_ALIAS_RESOLVED": "terminal written as an abbreviation, mapped by pattern",
    "TERMINAL_UNPARSEABLE": "terminal value does not match any known terminal pattern",
    "CARRIER_MALFORMED": "carrier_code is not a 2-10 character alphanumeric SCAC-style code",
    "TIMESTAMP_UNPARSEABLE": "timestamp matches none of the accepted inbound formats",
    "TIMESTAMP_MISSING": "timestamp is empty in the source export",
    "EVENT_TYPE_MISSING": "event_type is empty in the source export",
    "TERMINAL_MISSING": "terminal is empty in the source export",
}


def report(records, stream=sys.stdout):
    def w(line=""):
        print(line, file=stream)

    total = len(records)
    loadable = sum(1 for r in records if r["loadable"])

    w("=" * 68)
    w("DISPATCH EXCEPTION TRIAGE - NORMALIZATION REPORT")
    w("Corrigan Peak Logistics / Ajaia  https://ajaia.ai")
    w("=" * 68)
    w()
    w(f"Records in:        {total}")
    w(f"Records out:       {total}   (no record is dropped, ever)")
    w(f"Safe to load:      {loadable}")
    w(f"Held for review:   {total - loadable}")
    w()

    w("EXCEPTION COUNT BY EVENT TYPE")
    w("-" * 68)
    counts = Counter(r["event_type"] or "(missing)" for r in records)
    for event_type, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        w(f"  {event_type:<28} {n}")
    w(f"  {'TOTAL':<28} {sum(counts.values())}")
    w()

    w("COUNT BY TERMINAL")
    w("-" * 68)
    for terminal, n in sorted(Counter(r["terminal"] or "(missing)" for r in records).items()):
        w(f"  {terminal:<28} {n}")
    w()

    held = [r for r in records if not r["loadable"]]
    w("RECORDS NOT CLEANED WITH CONFIDENCE")
    w("-" * 68)
    if not held:
        w("  none")
    for r in held:
        w(f"  {r['exception_id']}")
        for flag in r["flags"].split("|"):
            if flag in BLOCKING:
                w(f"      {flag}: {FLAG_REASONS.get(flag, 'see flag')}")
    w()

    advisory = sorted({f for r in records for f in r["flags"].split("|")
                       if f and f not in BLOCKING})
    w("ADVISORY FLAGS (cleaned, but with a stated assumption)")
    w("-" * 68)
    for flag in advisory:
        ids = [r["exception_id"] for r in records if flag in r["flags"].split("|")]
        w(f"  {flag}  ({len(ids)}: {', '.join(ids)})")
        w(f"      {FLAG_REASONS.get(flag, '')}")
    w()

    unconfirmed = [r["exception_id"] for r in records if not r["tz_confirmed"]]
    if unconfirmed:
        w("!! OPEN QUESTION FOR CORRIGAN PEAK IT (feeds DET-121)")
        w("-" * 68)
        w(f"   {len(unconfirmed)} of {total} timestamps carry no timezone: "
          f"{', '.join(unconfirmed)}")
        w("   One record (CPX-88215) is explicitly UTC, so the feed is not")
        w("   internally consistent. Until Terminal 3's local zone is confirmed,")
        w("   any urgency score based on elapsed time may be off by hours.")
        w("   Ask: are naive stamps terminal-local, and what zone is Terminal 3?")
        w("   Ask: is MM/DD/YYYY guaranteed, or can DD/MM/YYYY appear?")
        w()
    w("=" * 68)


def write_csv(records, path):
    fields = ["exception_id", "terminal", "event_type", "carrier_code",
              "event_ts", "tz_confirmed", "loadable", "flags"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow({k: ("" if r[k] is None else r[k]) for k in fields})


# ---------------------------------------------------------------------------
# Self-test. Proves behaviour, not just absence of a crash.
# ---------------------------------------------------------------------------

def self_test():
    checks = []

    def check(name, condition):
        checks.append((name, bool(condition)))

    # Case handling on carrier codes.
    check("swft/SWFT/Swft all collapse to SWFT",
          {normalize_carrier(v)[0] for v in ["swft", "SWFT", "Swft", " swft "]} == {"SWFT"})

    # Terminal aliasing.
    check("'Terminal 3' -> TERMINAL_3", normalize_terminal("Terminal 3")[0] == "TERMINAL_3")
    check("'T3' -> TERMINAL_3", normalize_terminal("T3")[0] == "TERMINAL_3")
    check("'T3' is flagged as an alias resolution",
          "TERMINAL_ALIAS_RESOLVED" in normalize_terminal("T3")[1])

    # Three inbound timestamp shapes land on the same instant, wall-clock wise.
    check("slash format parses to the right wall time",
          normalize_timestamp("08/14/2026 09:45")[0] == "2026-08-14T09:45:00")
    check("dash format parses to the right wall time",
          normalize_timestamp("2026-08-14 09:12:00")[0] == "2026-08-14T09:12:00")
    check("Z format is carried through as UTC",
          normalize_timestamp("2026-08-14T10:03:00Z")[0] == "2026-08-14T10:03:00+00:00")

    # The judgment calls.
    check("naive timestamp is NOT silently stamped UTC",
          "+00:00" not in normalize_timestamp("2026-08-14 09:12:00")[0])
    check("naive timestamp is flagged TZ_UNCONFIRMED",
          "TZ_UNCONFIRMED" in normalize_timestamp("2026-08-14 09:12:00")[1])
    check("minute-precision input is flagged SECONDS_IMPUTED",
          "SECONDS_IMPUTED" in normalize_timestamp("08/14/2026 09:45")[1])
    check("blank carrier returns None, not a placeholder string",
          normalize_carrier("")[0] is None)
    check("blank carrier is flagged CARRIER_MISSING",
          "CARRIER_MISSING" in normalize_carrier("")[1])

    # Garbage in should be flagged, not coerced into something plausible.
    check("unparseable timestamp is flagged, original preserved",
          normalize_timestamp("last tuesday") == ("last tuesday", ["TIMESTAMP_UNPARSEABLE"]))
    check("unknown terminal string is flagged, not force-mapped",
          "TERMINAL_UNPARSEABLE" in normalize_terminal("Yard B")[1])

    # End to end against the real export.
    with open("exceptions_raw.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    records = process(rows)

    check("no record is dropped (5 in, 5 out)", len(rows) == len(records) == 5)
    check("no exception_id is lost or duplicated",
          sorted(r["exception_id"] for r in records) ==
          ["CPX-88213", "CPX-88214", "CPX-88215", "CPX-88216", "CPX-88217"])
    counts = Counter(r["event_type"] for r in records)
    check("counts: missed_pickup=2", counts["missed_pickup"] == 2)
    check("counts: doc_mismatch=2", counts["doc_mismatch"] == 2)
    check("counts: carrier_substitution=1", counts["carrier_substitution"] == 1)
    check("counts sum back to the input row count", sum(counts.values()) == len(rows))
    check("all five records resolve to TERMINAL_3",
          {r["terminal"] for r in records} == {"TERMINAL_3"})
    check("exactly one record is held for review (CPX-88216)",
          [r["exception_id"] for r in records if not r["loadable"]] == ["CPX-88216"])
    check("exactly one record has a confirmed timezone (CPX-88215)",
          [r["exception_id"] for r in records if r["tz_confirmed"]] == ["CPX-88215"])

    # Every emitted timestamp must survive a round trip back into a datetime.
    round_trips = all(
        datetime.fromisoformat(r["event_ts"]) is not None
        for r in records if r["event_ts"]
    )
    check("every normalized timestamp re-parses as ISO 8601", round_trips)

    # Idempotence: cleaning cleaned data changes nothing.
    twice = process([{k: ("" if r[k] is None else str(r[k])) for k in
                      ["exception_id", "terminal", "event_type", "carrier_code", "event_ts"]}
                     for r in records])
    check("normalization is idempotent (second pass is a no-op)",
          [r["event_ts"] for r in twice] == [r["event_ts"] for r in records])

    width = max(len(n) for n, _ in checks)
    print("SELF-TEST")
    print("-" * (width + 10))
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    failed = [n for n, ok in checks if not ok]
    print("-" * (width + 10))
    print(f"{len(checks) - len(failed)}/{len(checks)} passed")
    return 0 if not failed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("infile", nargs="?", default="exceptions_raw.csv")
    parser.add_argument("--out", default="exceptions_clean.csv")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    with open(args.infile, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    records = process(rows)
    report(records)
    write_csv(records, args.out)
    print(f"Cleaned records written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## Appendix B. `exceptions_clean.csv` (script output)

```csv
exception_id,terminal,event_type,carrier_code,event_ts,tz_confirmed,loadable,flags
CPX-88213,TERMINAL_3,missed_pickup,SWFT,2026-08-14T09:12:00,False,True,TZ_UNCONFIRMED
CPX-88214,TERMINAL_3,doc_mismatch,SWFT,2026-08-14T09:45:00,False,True,SECONDS_IMPUTED|TZ_UNCONFIRMED
CPX-88215,TERMINAL_3,missed_pickup,SWFT,2026-08-14T10:03:00+00:00,True,True,TERMINAL_ALIAS_RESOLVED
CPX-88216,TERMINAL_3,doc_mismatch,,2026-08-14T11:47:00,False,False,CARRIER_MISSING|TZ_UNCONFIRMED
CPX-88217,TERMINAL_3,carrier_substitution,RLCX,2026-08-15T08:02:00,False,True,SECONDS_IMPUTED|TZ_UNCONFIRMED
```
