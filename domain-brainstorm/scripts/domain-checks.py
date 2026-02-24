#!/usr/bin/env python3
"""Check domain availability via RDAP.

Usage:
  domain-checks.py -t <tld> [-t <tld> ...] -n <names>

  -t    TLD to check (repeat up to 3 times)
  -n    Comma-separated names, a file path (one name per line), or - for stdin

Output:
  stdout  One bare domain per line for each available domain (pipeable).
  stderr  Progress, errors, and a final summary.

Examples:
  ./domain-checks.py -t app -t io -n Bolt,Warp,Dash
  ./domain-checks.py -t app -n names.txt
  echo "Bolt,Warp,Dash" | ./domain-checks.py -t app -n -
  ./domain-checks.py -t app -n Bolt,Warp | xargs -I{} echo "Register: {}"
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Tuple

SLEEP_SECONDS = 0.6
TIMEOUT_SECONDS = 12
RETRIES = 2
BACKOFF_SECONDS = 2.0
RDAP_BASE = "https://rdap.org/domain/"
MAX_TLDS = 3
MAX_NAMES = 100


@dataclass
class Result:
    domain: str
    status: str  # AVAILABLE / TAKEN / UNKNOWN
    note: str = ""


def parse_csv(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def dedupe_lower(xs: List[str]) -> List[str]:
    seen: set = set()
    out = []
    for x in xs:
        x = x.strip().lower()
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def http_get_status(url: str) -> Tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/rdap+json, application/json;q=0.9, */*;q=0.1",
            "User-Agent": "rdap-domain-check/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return resp.getcode(), resp.read(512).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(512).decode("utf-8", errors="replace")
        except Exception:
            pass
        return int(e.code), body
    except urllib.error.URLError as e:
        return 0, f"URLError: {e}"
    except ssl.SSLError as e:
        return 0, f"SSLError: {e}"
    except Exception as e:
        return 0, f"Error: {e!r}"


def classify(domain: str) -> Result:
    url = RDAP_BASE + domain
    last_note = ""

    for attempt in range(RETRIES + 1):
        code, body = http_get_status(url)

        if code == 404:
            return Result(domain, "AVAILABLE")
        if code == 200:
            return Result(domain, "TAKEN")

        if code == 429:
            last_note = "rate limited (429)"
        elif code == 403:
            last_note = "blocked/forbidden (403)"
        elif 500 <= code <= 599:
            last_note = f"server error ({code})"
        elif code == 0:
            last_note = body or "network error"
        else:
            last_note = f"unexpected status ({code})"

        if body.strip().startswith("{"):
            try:
                j = json.loads(body)
                if isinstance(j, dict) and "title" in j:
                    last_note += f" - {j['title']}"
            except Exception:
                pass

        if attempt < RETRIES:
            time.sleep(BACKOFF_SECONDS * (attempt + 1))

    return Result(domain, "UNKNOWN", last_note)


def err(msg: str) -> None:
    sys.stderr.write(msg)
    sys.stderr.flush()


def progress(i: int, total: int) -> None:
    err(f"\r[{i}/{total}] checking...".ljust(30))


def clear_progress() -> None:
    err("\r" + " " * 30 + "\r")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-t", "--tld", dest="tlds", action="append", metavar="TLD",
        help=f"TLD to check (repeat up to {MAX_TLDS} times)",
    )
    parser.add_argument(
        "-n", "--names",
        help=f"Comma-separated names, a file path, or - for stdin (up to {MAX_NAMES})",
        required=True,
    )
    args = parser.parse_args()

    tlds = dedupe_lower(args.tlds or [])
    if not tlds:
        parser.error("Provide at least one TLD with -t.")
    if len(tlds) > MAX_TLDS:
        parser.error(f"At most {MAX_TLDS} TLDs allowed (got {len(tlds)}).")

    if args.names == "-":
        raw = [line.strip() for line in sys.stdin if line.strip()]
    elif os.path.isfile(args.names):
        with open(args.names) as f:
            raw = [line.strip() for line in f if line.strip()]
    else:
        raw = parse_csv(args.names)

    names = dedupe_lower(raw)
    if not names:
        parser.error("No names provided.")
    if len(names) > MAX_NAMES:
        parser.error(f"At most {MAX_NAMES} names allowed (got {len(names)}).")

    total = len(names) * len(tlds)
    available: List[str] = []
    errors: List[Result] = []

    for i, (name, tld) in enumerate(
        ((n, t) for n in names for t in tlds), start=1
    ):
        domain = f"{name}.{tld}"
        progress(i, total)
        res = classify(domain)

        if res.status == "AVAILABLE":
            clear_progress()
            print(res.domain, flush=True)
            available.append(res.domain)
        elif res.status == "UNKNOWN":
            clear_progress()
            err(f"ERROR: {res.domain} -> {res.note}\n")
            errors.append(res)

        if i < total:
            time.sleep(SLEEP_SECONDS)

    clear_progress()
    err(f"Done. {total} checked, {len(available)} available, {len(errors)} errors.\n")

    if errors:
        counts: Dict[str, int] = {}
        for e in errors:
            counts[e.note] = counts.get(e.note, 0) + 1
        err("\nError breakdown:\n")
        for note, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            err(f"  {n}x  {note}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
