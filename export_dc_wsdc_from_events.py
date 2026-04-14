#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Выгрузка танцоров с WSDC номерами из финальных результатов danceConvention.net
по списку ивентов (final-round-results).

Учётные данные:
  set DC_EMAIL=...
  set DC_PASSWORD=...

Использование:
  python export_dc_wsdc_from_events.py
  python export_dc_wsdc_from_events.py --out dc_wsdc_2025.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests

BASE = "https://danceconvention.net/eventdirector/rest"

# Ивенты: (ключ для отчёта, event_id) — подобраны по названиям из events-feed
DEFAULT_EVENTS: List[tuple[str, int]] = [
    ("Swing_and_Snow_2025", 300047750),
    ("Swing_and_Snow_2026", 300804490),
    ("Moscow_Westie_Fest_Gala_2025", 300632160),
    ("Sea_Dance_Fest_2025", 300698151),
    ("Americano_Dance_Camp_2025", 300139570),
    ("SPb_WCS_Nights_2025", 300454680),
    ("Honey_Fest_2025", 300225910),
]


def login(session: requests.Session, email: str, password: str) -> None:
    r = session.post(
        f"{BASE}/v2/auth/login",
        data={"email": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    sid = data.get("sessionId")
    if not sid:
        raise RuntimeError("login: no sessionId in response")
    session.cookies.set("DCNET_SESSION", sid, domain="danceconvention.net")


def get_json(session: requests.Session, path: str) -> Any:
    r = session.get(f"{BASE}{path}", timeout=60)
    if r.status_code == 401:
        raise RuntimeError(f"Unauthorized: {path}")
    r.raise_for_status()
    return r.json()


def fetch_event_competitions(session: requests.Session, event_id: int) -> Dict[str, Any]:
    return get_json(session, f"/v2/events/{event_id}")


def fetch_final_results(session: requests.Session, contest_id: int) -> Dict[str, Any]:
    return get_json(session, f"/v2/results/final-round-results/{contest_id}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default="dc_wsdc_events_export.csv",
        help="CSV output path",
    )
    args = ap.parse_args()

    email = os.environ.get("DC_EMAIL", "").strip()
    password = os.environ.get("DC_PASSWORD", "").strip()
    if not email or not password:
        print("Set DC_EMAIL and DC_PASSWORD", file=sys.stderr)
        return 1

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Dashboard_content/export_dc_wsdc_from_events.py",
            "Accept": "application/json",
        }
    )
    login(session, email, password)

    rows: List[Dict[str, Any]] = []
    for tag, event_id in DEFAULT_EVENTS:
        try:
            ev = fetch_event_competitions(session, event_id)
        except Exception as e:
            print(f"[skip] event {tag} id={event_id}: {e}", file=sys.stderr)
            time.sleep(0.3)
            continue

        ev_info = ev.get("eventInfo") or {}
        event_name = ev_info.get("name") or str(event_id)
        comps = ev.get("competitions") or []

        for c in comps:
            if c.get("affiliationType") != "WSDC":
                continue
            cid = c.get("contestId")
            cname = c.get("name") or ""
            if cid is None:
                continue
            try:
                fr = fetch_final_results(session, int(cid))
            except Exception as e:
                print(
                    f"[skip] final {tag} contest={cname} id={cid}: {e}",
                    file=sys.stderr,
                )
                time.sleep(0.2)
                continue

            results = fr.get("results") or []
            for line in results:
                rows.append(
                    {
                        "event_tag": tag,
                        "event_id": event_id,
                        "event_name": event_name,
                        "contest_id": cid,
                        "contest_name": cname,
                        "rank": line.get("rank"),
                        "bib_number": line.get("bibNumber"),
                        "competitor_role": line.get("competitorRole"),
                        "competitor_name": line.get("competitorName"),
                        "partner_name": line.get("partnerName"),
                        "affiliation_type": line.get("affiliationType"),
                        "wsdc_id": line.get("affiliationNumber"),
                    }
                )
            time.sleep(0.15)

        print(f"OK {tag} ({event_name}): competitions WSDC processed", file=sys.stderr)

    if not rows:
        print("No rows — check event IDs or login.", file=sys.stderr)
        return 2

    fieldnames = list(rows[0].keys())
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # Уникальные WSDC id (непустые)
    seen: Dict[str, tuple] = {}
    for r in rows:
        wid = (r.get("wsdc_id") or "").strip()
        if not wid:
            continue
        key = f"{wid}|{r.get('competitor_name','')}"
        if key not in seen:
            seen[key] = (wid, r.get("competitor_name"), r.get("event_name"))

    summary_path = args.out.replace(".csv", "_unique_wsdc.csv")
    def _sort_key(t: tuple) -> tuple:
        wid, name, _evn = t
        try:
            return (0, int(str(wid)))
        except ValueError:
            return (1, str(wid), name or "")

    with open(summary_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["wsdc_id", "competitor_name", "sample_event"])
        for wid, name, evn in sorted(seen.values(), key=_sort_key):
            w.writerow([wid, name, evn])

    print(f"Wrote {args.out} ({len(rows)} rows)", file=sys.stderr)
    print(f"Wrote {summary_path} ({len(seen)} unique wsdc ids)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
