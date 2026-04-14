#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
По списку wsdc_id из выгрузки danceConvention (CSV) запрашивает реестр WSDC
(points.worldsdc.com /lookup2020/find) и сохраняет:
  - построчно каждое начисление очков (ивент, дата, место, очки);
  - сводку по дивизиону и роли (всего очков, первый/последний ивент).

Вход по умолчанию: dc_wsdc_events_export.csv (колонка wsdc_id).

  python fetch_wsdc_registry_from_dc_export.py
  python fetch_wsdc_registry_from_dc_export.py --input dc_wsdc_events_export.csv --limit 20

Пауза между танцорами — как в wsdc_from_google_sheet (не дёргать реестр слишком часто).
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from wsdc_from_google_sheet import HEADERS, REQUEST_DELAY_MAX, REQUEST_DELAY_MIN, WSDC_LOOKUP_URL

FIND_URL = "https://points.worldsdc.com/lookup2020/find"


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in (
        "%B %Y",
        "%b %Y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
    ):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def get_csrf_token(session: requests.Session) -> str:
    r = session.get(WSDC_LOOKUP_URL, headers=HEADERS, timeout=45)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if not token_input or not token_input.get("value"):
        raise RuntimeError("CSRF _token not found on lookup2020 page")
    return str(token_input["value"])


def fetch_find_json(session: requests.Session, token: str, wsdc_id: int) -> Any:
    r = session.post(
        FIND_URL,
        data={"_token": token, "num": wsdc_id},
        headers=HEADERS,
        timeout=45,
    )
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return None


def extract_registry_name(data: Dict[str, Any]) -> str:
    for key in ("leader", "follower"):
        block = data.get(key) or {}
        d = block.get("dancer") or {}
        fn = (d.get("first_name") or "").strip()
        ln = (d.get("last_name") or "").strip()
        if fn or ln:
            return f"{fn} {ln}".strip()
    return ""


def iter_division_blocks(
    placements: Any,
) -> Iterable[Tuple[str, str, Dict[str, Any]]]:
    """
    Yields (dance_style, division_abbr, div_data dict).
    placements — как в JSON WSDC: dict или иногда list (пустой — пропуск).
    """
    if isinstance(placements, list):
        for item in placements:
            if not isinstance(item, dict):
                continue
            abbr = str(item.get("abbr") or item.get("code") or item.get("division") or "")
            dance = str(item.get("dance_style") or item.get("style") or "West Coast Swing")
            if item.get("competitions") is not None or item.get("division"):
                yield dance, abbr, item
        return

    if not isinstance(placements, dict):
        return

    for dance_type, divisions in placements.items():
        if not isinstance(divisions, dict):
            continue
        for div_abbr, div_data in divisions.items():
            if isinstance(div_data, dict):
                yield str(dance_type), str(div_abbr), div_data


def collect_rows_for_dancer(wsdc_id: int, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Одна строка CSV на каждую запись competitions[]."""
    registry_name = extract_registry_name(data)
    out: List[Dict[str, Any]] = []

    for role_key, role_label in (("leader", "Leader"), ("follower", "Follower")):
        block = data.get(role_key) or {}
        if block.get("type") != "dancer":
            continue

        placements = block.get("placements")
        for dance_style, div_abbr, div_data in iter_division_blocks(placements):
            division_info = div_data.get("division") or {}
            division_name = division_info.get("name") or div_abbr
            total_div = div_data.get("total_points")
            comps = div_data.get("competitions") or []
            if not isinstance(comps, list):
                continue

            for comp in comps:
                if not isinstance(comp, dict):
                    continue
                ev = comp.get("event") or {}
                out.append(
                    {
                        "wsdc_id": wsdc_id,
                        "registry_name": registry_name,
                        "role": role_label,
                        "dance_style": dance_style,
                        "division_abbr": div_abbr,
                        "division_name": division_name,
                        "division_total_points": total_div,
                        "division_wscid": (division_info.get("wscid") or ""),
                        "event_date": (ev.get("date") or ""),
                        "event_name": (ev.get("name") or ""),
                        "event_location": (ev.get("location") or ""),
                        "event_url": (ev.get("url") or ""),
                        "event_id_registry": ev.get("id"),
                        "points": comp.get("points"),
                        "placement": comp.get("result"),
                    }
                )

    return out


def load_unique_wsdc_ids(path: str) -> List[int]:
    seen = set()
    order: List[int] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if "wsdc_id" not in (reader.fieldnames or []):
            raise SystemExit("CSV must have column wsdc_id")
        for row in reader:
            raw = (row.get("wsdc_id") or "").strip()
            if not raw:
                continue
            try:
                wid = int(float(raw))
            except ValueError:
                continue
            if wid not in seen:
                seen.add(wid)
                order.append(wid)
    return order


def build_summary(detail_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Сводка: (wsdc_id, role, division_name) — сумма очков из строк ивентов, первый/последний ивент."""
    groups: Dict[Tuple[int, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for r in detail_rows:
        key = (int(r["wsdc_id"]), str(r["role"]), str(r["division_name"]))
        groups[key].append(r)

    summary: List[Dict[str, Any]] = []
    for (wid, role, div_name), rows in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        dated = []
        for r in rows:
            dt = parse_date(r.get("event_date"))
            dated.append((dt or datetime.min, r))
        dated.sort(key=lambda x: x[0])
        pts = 0
        for _, r in dated:
            try:
                pts += int(r.get("points") or 0)
            except (TypeError, ValueError):
                pass
        first = dated[0][1] if dated else {}
        last = dated[-1][1] if dated else {}
        summary.append(
            {
                "wsdc_id": wid,
                "registry_name": first.get("registry_name", ""),
                "role": role,
                "division_name": div_name,
                "division_abbr": first.get("division_abbr", ""),
                "points_sum_events": pts,
                "events_count": len(rows),
                "first_event_date": first.get("event_date", ""),
                "first_event_name": first.get("event_name", ""),
                "last_event_date": last.get("event_date", ""),
                "last_event_name": last.get("event_name", ""),
            }
        )
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="dc_wsdc_events_export.csv")
    ap.add_argument("--detail-out", default="wsdc_registry_placements_from_dc_export.csv")
    ap.add_argument("--summary-out", default="wsdc_registry_divisions_from_dc_export.csv")
    ap.add_argument("--failed-out", default="wsdc_registry_fetch_failed.txt")
    ap.add_argument("--limit", type=int, default=0, help="0 = all unique ids")
    args = ap.parse_args()

    ids = load_unique_wsdc_ids(args.input)
    if args.limit and args.limit > 0:
        ids = ids[: args.limit]

    if not ids:
        print("No wsdc_id values in input.", file=sys.stderr)
        return 1

    session = requests.Session()
    session.headers.update(HEADERS)

    detail_all: List[Dict[str, Any]] = []
    failed: List[str] = []

    token = get_csrf_token(session)
    print(f"Loaded {len(ids)} unique wsdc_id from {args.input}", flush=True)

    for i, wid in enumerate(ids, start=1):
        try:
            data = fetch_find_json(session, token, wid)
            if not data or not isinstance(data, dict):
                failed.append(f"{wid}\tempty_or_non_json")
                continue
            rows = collect_rows_for_dancer(wid, data)
            detail_all.extend(rows)
            if i % 25 == 0 or i == 1:
                print(f"  [{i}/{len(ids)}] wsdc_id={wid} rows={len(rows)}", flush=True)
        except Exception as e:
            failed.append(f"{wid}\t{e}")
            try:
                token = get_csrf_token(session)
            except Exception:
                pass
        time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

    if detail_all:
        fieldnames = list(detail_all[0].keys())
        with open(args.detail_out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(detail_all)

    summary = build_summary(detail_all)
    if summary:
        with open(args.summary_out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
            w.writeheader()
            w.writerows(summary)

    if failed:
        with open(args.failed_out, "w", encoding="utf-8") as f:
            f.write("\n".join(failed))

    print(f"Detail rows: {len(detail_all)} -> {args.detail_out}", flush=True)
    print(f"Summary rows: {len(summary)} -> {args.summary_out}", flush=True)
    if failed:
        print(f"Failed: {len(failed)} (see {args.failed_out})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
