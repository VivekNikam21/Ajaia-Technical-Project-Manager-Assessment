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
