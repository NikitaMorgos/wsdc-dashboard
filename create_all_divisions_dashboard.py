#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерирует все новые дашборды WSDC в папку charts/:

  charts/rating_dashboard.html        — рейтинг по всем дивизионам
  charts/time_in_division.html        — время прохождения дивизиона
  charts/speed_and_funnel.html        — скорость набора + воронка
  charts/tournament_results.html      — топ мест на турнирах

Использование:
  python create_all_divisions_dashboard.py
  python create_all_divisions_dashboard.py \\
      --divisions-csv  wsdc_registry_divisions_from_dc_export.csv \\
      --placements-csv wsdc_registry_placements_from_dc_export.csv \\
      --events-csv     dc_wsdc_events_export.csv \\
      --out-dir        charts
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Настройки
# ──────────────────────────────────────────────────────────────────────────────
THRESHOLDS: Dict[str, Optional[int]] = {
    "Newcomer":     10,
    "Novice":       16,
    "Intermediate": 30,
    "Advanced":     45,
    "All-Stars":    None,
    "Sophisticated": None,
    "Masters":      None,
}

DIVISION_ORDER = ["Newcomer", "Novice", "Intermediate", "Advanced",
                  "All-Stars", "Sophisticated", "Masters"]

DIVISION_INDEX = {d: i for i, d in enumerate(DIVISION_ORDER)}

# Основная лестница WSDC (одна строка на танцора, если нет Soph/Masters)
MAIN_LADDER_DIVISIONS = frozenset(
    {"Newcomer", "Novice", "Intermediate", "Advanced", "All-Stars"}
)
# Sophisticated / Masters — отдельные треки: не схлопываем с основной лестницей
SPECIAL_DIVISIONS = frozenset({"Sophisticated", "Masters"})

DIVISION_COLORS = {
    "Newcomer":     "#06b6d4",
    "Novice":       "#4361ee",
    "Intermediate": "#7209b7",
    "Advanced":     "#f72585",
    "All-Stars":    "#f4a261",
    "Sophisticated": "#2dc653",
    "Masters":      "#8b949e",
}

RULES_SOURCE = "WSDC Rulebook 2025"

# ──────────────────────────────────────────────────────────────────────────────
# Утилиты
# ──────────────────────────────────────────────────────────────────────────────
def parse_date(s: Optional[str]) -> Optional[datetime]:
    for fmt in ("%B %Y", "%b %Y", "%Y-%m-%d", "%m/%d/%Y",
                "%d/%m/%Y", "%Y/%m/%d", "%B %d, %Y"):
        try:
            return datetime.strptime((s or "").strip(), fmt)
        except ValueError:
            pass
    return None


def months_between(d1: datetime, d2: datetime) -> int:
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def jd(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False)


def today_str() -> str:
    return datetime.today().strftime("%d.%m.%Y")


# ──────────────────────────────────────────────────────────────────────────────
# Загрузка данных
# ──────────────────────────────────────────────────────────────────────────────
def load_divisions(path: str) -> List[Dict]:
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            fd = parse_date(r.get("first_event_date"))
            ld = parse_date(r.get("last_event_date"))
            pts = int(r.get("points_sum_events") or 0)
            evts = int(r.get("events_count") or 1)
            months = months_between(fd, ld) if fd and ld else None
            speed = round(pts / max(months, 1), 2) if months and months > 0 else None
            rows.append({
                "wsdc_id":   r.get("wsdc_id", ""),
                "name":      r.get("registry_name", ""),
                "role":      r.get("role", ""),
                "division":  r.get("division_name", ""),
                "abbr":      r.get("division_abbr", ""),
                "points":    pts,
                "events":    evts,
                "first":     r.get("first_event_date", ""),
                "last":      r.get("last_event_date", ""),
                "first_dt":  fd,
                "last_dt":   ld,
                "months":    months,
                "speed":     speed,
            })
    return rows


def _normalize_role(role: str) -> str:
    r = (role or "").strip()
    u = r.upper()
    if u == "LEADER":
        return "Leader"
    if u == "FOLLOWER":
        return "Follower"
    return r


def infer_division_from_contest_name(contest_name: str) -> Optional[str]:
    """Грубое сопоставление названия конкурса DC с дивизионом WSDC."""
    s = (contest_name or "").lower()
    # Сначала более специфичные / отдельные треки
    if "sophisticated" in s:
        return "Sophisticated"
    if "masters" in s or " master" in s:
        return "Masters"
    if "all star" in s or "allstar" in s or "all-star" in s:
        return "All-Stars"
    if "advanced" in s:
        return "Advanced"
    if "intermediate" in s:
        return "Intermediate"
    if "novice" in s:
        return "Novice"
    if "newcomer" in s:
        return "Newcomer"
    return None


def build_rating_rows(div_rows: List[Dict]) -> List[Dict]:
    """
    Рейтинг «текущий дивизион»:
    - Без Soph/Masters: одна строка — самый старший из Newcomer…All-Stars.
    - Если в реестре есть Sophisticated и/или Masters: все строки основной лестницы
      + Soph + Masters (дубли между уровнями разрешены).
    """
    groups: Dict[Tuple[str, str], List[Dict]] = defaultdict(list)
    for r in div_rows:
        wid = (r.get("wsdc_id") or "").strip()
        if not wid:
            continue
        role = (r.get("role") or "").strip()
        groups[(wid, role)].append(r)

    out: List[Dict] = []
    for rows in groups.values():
        main_rows = [r for r in rows if r.get("division") in MAIN_LADDER_DIVISIONS]
        spl_rows = [r for r in rows if r.get("division") in SPECIAL_DIVISIONS]
        has_spl = bool(spl_rows)

        if has_spl:
            out.extend(main_rows)
            out.extend(spl_rows)
        else:
            if main_rows:
                best = max(
                    main_rows,
                    key=lambda r: (DIVISION_INDEX.get(r["division"], -1), r["points"]),
                )
                out.append(best)
            else:
                out.extend(spl_rows)
    return out


def _max_main_ladder_index_by_pair(div_rows: List[Dict]) -> Dict[Tuple[str, str], int]:
    """Максимальный индекс дивизиона на основной лестнице (по реестру), или -1 если нет."""
    m: Dict[Tuple[str, str], int] = {}
    for r in div_rows:
        wid = (r.get("wsdc_id") or "").strip()
        if not wid:
            continue
        role = (r.get("role") or "").strip()
        div = r.get("division") or ""
        if div not in MAIN_LADDER_DIVISIONS:
            continue
        idx = DIVISION_INDEX[div]
        k = (wid, role)
        if idx > m.get(k, -1):
            m[k] = idx
    return m


def add_zero_point_rows_from_events(
    rating_rows: List[Dict],
    events_csv_path: str,
    div_rows: List[Dict],
) -> List[Dict]:
    """
    Добавляет строки с 0 очков по dc_wsdc_events_export, если пары (wsdc_id, role, division)
    ещё нет в рейтинге. Не добавляет дивизион **ниже** уже зафиксированного в реестре
    по основной лестнице (иначе Intermediate оказывался бы и в Novice из старого конкурса).
    """
    max_main = _max_main_ladder_index_by_pair(div_rows)

    def key(r: Dict) -> Tuple[str, str, str]:
        return (
            (r.get("wsdc_id") or "").strip(),
            (r.get("role") or "").strip(),
            r.get("division") or "",
        )

    existing = {key(r) for r in rating_rows}
    extra: Dict[Tuple[str, str, str], Dict] = {}

    try:
        with open(events_csv_path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                wid = (r.get("wsdc_id") or "").strip()
                if not wid:
                    continue
                role = _normalize_role(r.get("competitor_role", ""))
                if role not in ("Leader", "Follower"):
                    continue
                div = infer_division_from_contest_name(r.get("contest_name", ""))
                if not div or div not in DIVISION_INDEX:
                    continue
                if div in MAIN_LADDER_DIVISIONS:
                    hi = max_main.get((wid, role), -1)
                    lo = DIVISION_INDEX[div]
                    if hi > lo:
                        continue
                k = (wid, role, div)
                if k in existing:
                    continue
                if k not in extra:
                    extra[k] = {
                        "wsdc_id":   wid,
                        "name":      r.get("competitor_name", "") or wid,
                        "role":      role,
                        "division":  div,
                        "abbr":      "",
                        "points":    0,
                        "events":    0,
                        "first":     "",
                        "last":      "",
                        "first_dt":  None,
                        "last_dt":   None,
                        "months":    None,
                        "speed":     None,
                    }
                else:
                    nm = r.get("competitor_name", "").strip()
                    if nm and (not extra[k]["name"] or len(nm) > len(extra[k]["name"])):
                        extra[k]["name"] = nm
    except OSError:
        pass

    return rating_rows + list(extra.values())


def load_placements(path: str) -> List[Dict]:
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            dt = parse_date(r.get("event_date"))
            pts = 0
            try:
                pts = int(float(r.get("points") or 0))
            except (ValueError, TypeError):
                pass
            rows.append({
                "wsdc_id":   r.get("wsdc_id", ""),
                "name":      r.get("registry_name", ""),
                "role":      r.get("role", ""),
                "division":  r.get("division_name", ""),
                "event":     r.get("event_name", ""),
                "event_dt":  dt,
                "points":    pts,
                "placement": r.get("placement", ""),
            })
    return rows


def load_events(path: str) -> List[Dict]:
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            try:
                rank = int(r.get("rank") or 0)
            except (ValueError, TypeError):
                rank = 0
            rows.append({
                "wsdc_id":       (r.get("wsdc_id") or "").strip(),
                "name":          r.get("competitor_name", ""),
                "role":          (r.get("competitor_role") or "").title(),
                "event_name":    r.get("event_name", ""),
                "event_tag":     r.get("event_tag", ""),
                "contest_name":  r.get("contest_name", ""),
                "rank":          rank,
            })
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# Вычисление времени прохождения дивизиона (из placements)
# ──────────────────────────────────────────────────────────────────────────────
def compute_time_to_threshold(placements: List[Dict]) -> Dict[Tuple[str, str, str], Dict]:
    """
    Returns {(wsdc_id, role, division): {months, first_event, close_event, points_at_close}}
    """
    grouped: Dict[Tuple, List] = defaultdict(list)
    for p in placements:
        if p["event_dt"]:
            grouped[(p["wsdc_id"], p["role"], p["division"])].append(p)

    result: Dict[Tuple, Dict] = {}
    for key, evs in grouped.items():
        _, role, div = key
        thresh = THRESHOLDS.get(div)
        if not thresh:
            continue
        evs_sorted = sorted(evs, key=lambda x: x["event_dt"])
        cumul = 0
        first_dt = evs_sorted[0]["event_dt"]
        first_ev = evs_sorted[0]["event"]
        for ev in evs_sorted:
            cumul += ev["points"]
            if cumul >= thresh:
                close_dt = ev["event_dt"]
                mo = months_between(first_dt, close_dt)
                if mo >= 0:
                    result[key] = {
                        "months":       mo,
                        "first_event":  first_ev,
                        "first_date":   first_dt.strftime("%B %Y"),
                        "close_event":  ev["event"],
                        "close_date":   close_dt.strftime("%B %Y"),
                        "pts_at_close": cumul,
                    }
                break
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Общий HTML-каркас
# ──────────────────────────────────────────────────────────────────────────────
_COMMON_CSS = """
<style>
:root{--blue:#4361ee;--indigo:#3a0ca3;--purple:#7209b7;--pink:#f72585;
      --green:#2dc653;--amber:#f4a261;--cyan:#06b6d4;--red:#e63946;
      --dark:#0d1117;--card:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--dark);
     color:var(--text);line-height:1.6;padding:24px 16px 60px;}
a{color:var(--blue);text-decoration:none;}
a:hover{text-decoration:underline;}
.wrap{max-width:1200px;margin:0 auto;}
.page-header{text-align:center;padding:32px 0 40px;}
.page-header h1{font-size:2rem;font-weight:800;margin-bottom:8px;}
.page-header p{color:var(--muted);font-size:.95rem;}
.meta{font-size:.73rem;color:var(--muted);margin-top:6px;}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:24px;}
.section-title{font-size:1.25rem;font-weight:700;margin-bottom:18px;padding-bottom:10px;
               border-bottom:1px solid var(--border);}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px;}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
@media(max-width:900px){.grid2,.grid3,.grid4{grid-template-columns:1fr 1fr;}}
@media(max-width:560px){.grid2,.grid3,.grid4{grid-template-columns:1fr;}}
.stat-box{text-align:center;padding:18px;}
.stat-num{font-size:2.4rem;font-weight:800;line-height:1;}
.stat-lbl{font-size:.75rem;color:var(--muted);margin-top:4px;}
table{width:100%;border-collapse:collapse;font-size:.875rem;}
th{color:var(--muted);font-weight:600;text-align:left;padding:8px 12px;
   border-bottom:1px solid var(--border);white-space:nowrap;}
td{padding:8px 12px;border-bottom:1px solid rgba(48,54,61,.5);vertical-align:middle;}
tr:last-child td{border-bottom:none;}
tr:hover td{background:rgba(255,255,255,.03);}
.badge{display:inline-block;font-size:.68rem;font-weight:700;padding:3px 9px;
       border-radius:20px;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap;}
.prog-wrap{background:var(--border);border-radius:4px;height:7px;width:100%;min-width:60px;}
.prog-bar{height:7px;border-radius:4px;}
.tab-bar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:20px;}
.tab-btn{padding:7px 16px;border-radius:8px;border:1px solid var(--border);
         background:transparent;color:var(--muted);cursor:pointer;font-size:.82rem;
         transition:all .18s;}
.tab-btn:hover{color:var(--text);border-color:#555;}
.tab-btn.active{color:#fff;border-color:transparent;}
.role-btn{padding:6px 18px;border-radius:20px;border:1px solid var(--border);
          background:transparent;color:var(--muted);cursor:pointer;font-size:.82rem;
          transition:all .18s;}
.role-btn.active{background:var(--blue);color:#fff;border-color:var(--blue);}
.back-link{display:inline-flex;align-items:center;gap:6px;color:var(--muted);
           font-size:.83rem;margin-bottom:28px;border:1px solid var(--border);
           padding:6px 14px;border-radius:8px;transition:all .18s;}
.back-link:hover{color:var(--text);border-color:#555;text-decoration:none;}
.search-box{width:100%;background:var(--card);border:1px solid var(--border);
            border-radius:8px;color:var(--text);padding:9px 14px;font-size:.88rem;
            margin-bottom:16px;outline:none;}
.search-box:focus{border-color:var(--blue);}
.canvas-wrap{position:relative;height:340px;margin:8px 0 4px;}
.mb20{margin-bottom:20px;}
.mb32{margin-bottom:32px;}
.gold{color:#f6d365;} .silver{color:#c0c0c0;} .bronze{color:#cd7f32;}
.pts{font-weight:700;color:var(--blue);}
.rank-medal{font-size:1.1rem;}
</style>
"""


def _page(title: str, body: str, active_link: str = "") -> str:
    nav_links = [
        ("../charts/rating_dashboard.html", "🏅 Рейтинги"),
        ("../charts/time_in_division.html", "⏱ Время"),
        ("../charts/speed_and_funnel.html", "⚡ Скорость"),
        ("../charts/tournament_results.html", "🏆 Турниры"),
        ("../index.html", "🏠 Главная"),
    ]
    nav_html = ""
    for href, label in nav_links:
        cls = ' class="active"' if href == active_link else ""
        nav_html += f'<a href="{href}"{cls}>{label}</a>\n'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · WSDC Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
{_COMMON_CSS}
<style>
nav{{position:sticky;top:0;z-index:100;background:rgba(13,17,23,.94);
     backdrop-filter:blur(10px);border-bottom:1px solid var(--border);
     padding:10px 16px;display:flex;gap:6px;flex-wrap:wrap;}}
nav a{{font-size:.78rem;color:var(--muted);padding:5px 11px;border-radius:6px;
       border:1px solid transparent;transition:all .18s;}}
nav a:hover,nav a.active{{color:var(--text);border-color:var(--border);
                           background:var(--card);text-decoration:none;}}
</style>
</head>
<body>
<nav>{nav_html}</nav>
<div class="wrap">
{body}
</div>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# Дашборд 1: Рейтинги по дивизионам
# ──────────────────────────────────────────────────────────────────────────────
def build_rating_dashboard(div_rows: List[Dict]) -> str:
    # Группируем по дивизиону → роли
    data: Dict[str, Dict[str, List[Dict]]] = {}
    for div in DIVISION_ORDER:
        data[div] = {"Leader": [], "Follower": []}

    for r in div_rows:
        div = r["division"]
        role = r["role"]
        if div in data and role in data[div]:
            data[div][role].append(r)

    # Сортировка по очкам
    for div in data:
        for role in data[div]:
            data[div][role].sort(key=lambda x: -x["points"])

    # JS-данные
    js_data: Dict[str, Any] = {}
    for div in DIVISION_ORDER:
        thresh = THRESHOLDS.get(div)
        color = DIVISION_COLORS.get(div, "#4361ee")
        js_data[div] = {"threshold": thresh, "color": color, "Leader": [], "Follower": []}
        for role in ("Leader", "Follower"):
            for i, r in enumerate(data[div][role]):
                js_data[div][role].append({
                    "rank":    i + 1,
                    "name":    r["name"],
                    "wsdc_id": r["wsdc_id"],
                    "points":  r["points"],
                    "events":  r["events"],
                    "first":   r["first"],
                    "last":    r["last"],
                    "active":  1 if (thresh and r["points"] < thresh) else 0,
                })

    # Создаём вкладки
    tab_btns = ""
    tab_panels = ""
    for di, div in enumerate(DIVISION_ORDER):
        if not data[div]["Leader"] and not data[div]["Follower"]:
            continue
        color = DIVISION_COLORS.get(div, "#4361ee")
        tab_btns += f'<button class="tab-btn" data-div="{div}" onclick="switchDiv(this)" style="border-color:{color}30">{div}</button>\n'

    for div in DIVISION_ORDER:
        if not data[div]["Leader"] and not data[div]["Follower"]:
            continue

    body = f"""
<a href="../index.html" class="back-link">← Главная</a>
<div class="page-header">
  <h1>🏅 Рейтинг танцоров по дивизионам</h1>
  <p>WSDC Points Registry · {today_str()}</p>
  <p style="max-width:720px;margin:10px auto 0;color:var(--muted);font-size:.9rem;line-height:1.45">
    По основной лестнице (Newcomer → All-Stars) — один раз в самом старшем дивизионе, где есть очки в реестре.
    <strong>Sophisticated</strong> и <strong>Masters</strong> — отдельно: там полный список; если у танцора есть Soph/Masters,
    показываются и все его строки по основной лестнице. Участники с <strong>0</strong> очков — по конкурсам DC, если дивизион конкурса не ниже текущего в реестре.
  </p>
  <div class="meta">{RULES_SOURCE} · Источник: danceConvention + points.worldsdc.com</div>
</div>

<div class="card mb32">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
    <div class="tab-bar" id="divTabs">{tab_btns}</div>
    <div style="display:flex;gap:8px;">
      <button class="role-btn active" id="btnLeader" onclick="switchRole('Leader')">Leader</button>
      <button class="role-btn" id="btnFollower" onclick="switchRole('Follower')">Follower</button>
    </div>
  </div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;">
    <label style="display:flex;align-items:center;gap:6px;font-size:.82rem;color:var(--muted);cursor:pointer;">
      <input type="checkbox" id="chkActive" onchange="renderTable()" checked>
      Только активные (ниже порога)
    </label>
    <input class="search-box" id="searchBox" placeholder="Поиск по имени…" oninput="renderTable()"
           style="width:220px;margin:0;">
  </div>

  <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:20px;" id="statsRow"></div>

  <div class="canvas-wrap mb20">
    <canvas id="ratingChart"></canvas>
  </div>

  <div id="tableWrap"></div>
</div>

<script>
const ALL_DATA = {jd(js_data)};
let currentDiv = null;
let currentRole = 'Leader';

function initDefaultDiv() {{
  const order = {jd(DIVISION_ORDER)};
  for (const d of order) {{
    if (ALL_DATA[d] && (ALL_DATA[d].Leader.length || ALL_DATA[d].Follower.length)) {{
      return d;
    }}
  }}
  return null;
}}

window.onload = function() {{
  currentDiv = initDefaultDiv();
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(t => {{
    if (t.dataset.div === currentDiv) t.classList.add('active');
  }});
  renderAll();
}};

function switchDiv(btn) {{
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentDiv = btn.dataset.div;
  renderAll();
}}

function switchRole(role) {{
  currentRole = role;
  document.getElementById('btnLeader').classList.toggle('active', role === 'Leader');
  document.getElementById('btnFollower').classList.toggle('active', role === 'Follower');
  renderAll();
}}

let ratingChart = null;

function getFiltered() {{
  const divData = ALL_DATA[currentDiv];
  if (!divData) return [];
  let rows = divData[currentRole] || [];
  const onlyActive = document.getElementById('chkActive').checked;
  const thresh = divData.threshold;
  if (onlyActive && thresh) rows = rows.filter(r => r.active);
  const q = (document.getElementById('searchBox').value || '').toLowerCase();
  if (q) rows = rows.filter(r => r.name.toLowerCase().includes(q));
  return rows;
}}

function renderStats(rows) {{
  const divData = ALL_DATA[currentDiv] || {{}};
  const thresh = divData.threshold;
  const allRows = divData[currentRole] || [];
  const active = thresh ? allRows.filter(r => r.active) : allRows;
  const closed = thresh ? allRows.filter(r => !r.active) : [];
  const avgPts = allRows.length ? (allRows.reduce((s,r)=>s+r.points,0)/allRows.length).toFixed(1) : 0;
  const maxPts = allRows.length ? Math.max(...allRows.map(r=>r.points)) : 0;

  document.getElementById('statsRow').innerHTML = `
    <div class="card stat-box" style="flex:1;min-width:100px">
      <div class="stat-num" style="color:var(--blue)">${{allRows.length}}</div>
      <div class="stat-lbl">всего</div>
    </div>
    ${{thresh ? `<div class="card stat-box" style="flex:1;min-width:100px">
      <div class="stat-num" style="color:var(--amber)">${{active.length}}</div>
      <div class="stat-lbl">активных (< ${{thresh}} pts)</div>
    </div>
    <div class="card stat-box" style="flex:1;min-width:100px">
      <div class="stat-num" style="color:var(--green)">${{closed.length}}</div>
      <div class="stat-lbl">закрыли дивизион</div>
    </div>` : ''}}
    <div class="card stat-box" style="flex:1;min-width:100px">
      <div class="stat-num">${{avgPts}}</div>
      <div class="stat-lbl">среднее pts</div>
    </div>
    <div class="card stat-box" style="flex:1;min-width:100px">
      <div class="stat-num">${{maxPts}}</div>
      <div class="stat-lbl">максимум pts</div>
    </div>
  `;
}}

function renderChart(rows) {{
  const divData = ALL_DATA[currentDiv] || {{}};
  const color = divData.color || '#4361ee';
  const thresh = divData.threshold;
  const top = rows.slice(0, 40);

  const ctx = document.getElementById('ratingChart').getContext('2d');
  if (ratingChart) ratingChart.destroy();

  const barColors = top.map(r => r.active
    ? color + 'dd'
    : (thresh ? '#2dc65399' : color + 'dd'));

  ratingChart = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: top.map(r => r.name),
      datasets: [{{
        data: top.map(r => r.points),
        backgroundColor: barColors,
        borderRadius: 4,
      }},
      thresh ? {{
        type: 'line',
        data: Array(top.length).fill(thresh),
        borderColor: '#f7253588',
        borderWidth: 2,
        borderDash: [6,4],
        pointRadius: 0,
        label: 'Порог',
      }} : null
      ].filter(Boolean),
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }},
        tooltip: {{ callbacks: {{
          label: ctx => ' ' + ctx.parsed.y + ' pts',
        }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#8b949e', maxRotation: 45, font: {{size: 10}} }},
               grid: {{ color: '#21262d' }} }},
        y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }},
               beginAtZero: true }},
      }},
    }},
  }});
}}

function renderTable(rows) {{
  if (!rows) rows = getFiltered();
  const divData = ALL_DATA[currentDiv] || {{}};
  const thresh = divData.threshold;
  const color = divData.color || '#4361ee';

  let html = `<div style="overflow-x:auto;"><table>
    <thead><tr>
      <th>#</th><th>Имя</th><th>WSDC ID</th><th>Очки</th>
      ${{thresh ? '<th>Прогресс</th>' : ''}}
      <th>Ивентов</th><th>Первый</th><th>Последний</th>
    </tr></thead><tbody>`;

  rows.forEach((r, i) => {{
    const pct = thresh ? Math.min(r.points / thresh * 100, 100) : null;
    const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : (i+1);
    const rowStyle = i < 3 ? 'background:rgba(255,255,255,.03)' : '';
    html += `<tr style="${{rowStyle}}">
      <td><span style="font-weight:700">${{medal}}</span></td>
      <td style="font-weight:600">${{r.name}}</td>
      <td><a href="https://points.worldsdc.com/lookup2020?q=${{r.wsdc_id}}"
             target="_blank" style="color:var(--muted);font-size:.8rem">${{r.wsdc_id}}</a></td>
      <td class="pts">${{r.points}}</td>
      ${{thresh ? `<td style="min-width:100px">
        <div style="display:flex;align-items:center;gap:8px;">
          <div class="prog-wrap" style="flex:1">
            <div class="prog-bar" style="width:${{pct}}%;background:${{r.active ? color : '#2dc653'}}"></div>
          </div>
          <span style="font-size:.75rem;color:var(--muted);white-space:nowrap">
            ${{r.points}}/${{thresh}}
          </span>
        </div>
      </td>` : ''}}
      <td style="color:var(--muted)">${{r.events}}</td>
      <td style="color:var(--muted);font-size:.82rem">${{r.first}}</td>
      <td style="color:var(--muted);font-size:.82rem">${{r.last}}</td>
    </tr>`;
  }});
  html += '</tbody></table></div>';
  if (!rows.length) html = '<p style="color:var(--muted);padding:20px">Нет данных по выбранным фильтрам.</p>';
  document.getElementById('tableWrap').innerHTML = html;
}}

function renderAll() {{
  const rows = getFiltered();
  renderStats(rows);
  renderChart(rows);
  renderTable(rows);
}}
</script>
"""
    return _page("Рейтинги по дивизионам", body, "../charts/rating_dashboard.html")


# ──────────────────────────────────────────────────────────────────────────────
# Дашборд 2: Время в дивизионе
# ──────────────────────────────────────────────────────────────────────────────
def build_time_dashboard(div_rows: List[Dict], placements: List[Dict]) -> str:
    time_data = compute_time_to_threshold(placements)

    # Обогащаем имена из div_rows
    names: Dict[str, str] = {}
    for r in div_rows:
        names[r["wsdc_id"]] = r["name"]

    js_data: Dict[str, Any] = {}
    for div in DIVISION_ORDER:
        thresh = THRESHOLDS.get(div)
        if not thresh:
            continue
        js_data[div] = {"threshold": thresh, "color": DIVISION_COLORS.get(div, "#4361ee"),
                         "Leader": [], "Follower": []}
        for role in ("Leader", "Follower"):
            entries = []
            for (wid, r, d), info in time_data.items():
                if d == div and r == role:
                    entries.append({
                        "wsdc_id":    wid,
                        "name":       names.get(wid, wid),
                        "months":     info["months"],
                        "first_date": info["first_date"],
                        "first_ev":   info["first_event"],
                        "close_date": info["close_date"],
                        "close_ev":   info["close_event"],
                    })
            entries.sort(key=lambda x: x["months"])
            js_data[div][role] = entries

    # Вычислить статистику для каждого дивизиона × роли
    stats_js: Dict[str, Any] = {}
    for div, ddata in js_data.items():
        stats_js[div] = {}
        for role in ("Leader", "Follower"):
            vals = [e["months"] for e in ddata[role]]
            if vals:
                stats_js[div][role] = {
                    "n":      len(vals),
                    "median": statistics.median(vals),
                    "mean":   round(statistics.mean(vals), 1),
                    "min":    min(vals),
                    "max":    max(vals),
                    "p25":    sorted(vals)[int(len(vals) * 0.25)],
                    "p75":    sorted(vals)[int(len(vals) * 0.75)],
                }
            else:
                stats_js[div][role] = None

    body = f"""
<a href="../index.html" class="back-link">← Главная</a>
<div class="page-header">
  <h1>⏱ Время прохождения дивизиона</h1>
  <p>От первого очка до достижения порога перехода · {today_str()}</p>
  <div class="meta">{RULES_SOURCE} · Newcomer 10pts · Novice 16pts · Intermediate 30pts · Advanced 45pts</div>
</div>

<div class="card mb32">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px;">
    <div class="tab-bar" id="divTabs">
      {''.join(f'<button class="tab-btn" data-div="{d}" onclick="switchDiv(this)">{d}</button>' for d in js_data)}
    </div>
    <div style="display:flex;gap:8px;">
      <button class="role-btn active" id="btnLeader" onclick="switchRole(\'Leader\')">Leader</button>
      <button class="role-btn" id="btnFollower" onclick="switchRole(\'Follower\')">Follower</button>
    </div>
  </div>

  <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px;" id="statsRow"></div>

  <div class="grid2 mb32">
    <div>
      <div style="font-size:.85rem;color:var(--muted);margin-bottom:8px;">Распределение (гистограмма)</div>
      <div class="canvas-wrap"><canvas id="histChart"></canvas></div>
    </div>
    <div>
      <div style="font-size:.85rem;color:var(--muted);margin-bottom:8px;">Leader vs Follower</div>
      <div class="canvas-wrap"><canvas id="compareChart"></canvas></div>
    </div>
  </div>

  <h3 class="section-title">Топ быстрых закрытий</h3>
  <div id="fastTable"></div>
  <h3 class="section-title" style="margin-top:24px">Все закрытия — по возрастанию</h3>
  <div id="allTable"></div>
</div>

<script>
const TIME_DATA = {jd(js_data)};
const STATS = {jd(stats_js)};
let curDiv = Object.keys(TIME_DATA)[0];
let curRole = 'Leader';
let histChart = null, cmpChart = null;

window.onload = function() {{
  document.querySelector('.tab-btn').classList.add('active');
  renderAll();
}};

function switchDiv(btn) {{
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  curDiv = btn.dataset.div;
  renderAll();
}}
function switchRole(r) {{
  curRole = r;
  document.getElementById('btnLeader').classList.toggle('active', r==='Leader');
  document.getElementById('btnFollower').classList.toggle('active', r==='Follower');
  renderAll();
}}

function renderStats() {{
  const st = STATS[curDiv] && STATS[curDiv][curRole];
  const div_info = TIME_DATA[curDiv];
  const color = div_info ? div_info.color : '#4361ee';
  if (!st) {{
    document.getElementById('statsRow').innerHTML = '<p style="color:var(--muted)">Недостаточно данных</p>';
    return;
  }}
  document.getElementById('statsRow').innerHTML = `
    <div class="card stat-box" style="flex:1;min-width:90px">
      <div class="stat-num" style="color:${{color}}">${{st.n}}</div>
      <div class="stat-lbl">закрыли дивизион</div>
    </div>
    <div class="card stat-box" style="flex:1;min-width:90px">
      <div class="stat-num">${{st.median}}</div>
      <div class="stat-lbl">медиана (мес)</div>
    </div>
    <div class="card stat-box" style="flex:1;min-width:90px">
      <div class="stat-num">${{st.mean}}</div>
      <div class="stat-lbl">среднее (мес)</div>
    </div>
    <div class="card stat-box" style="flex:1;min-width:90px">
      <div class="stat-num" style="color:var(--green)">${{st.min}}</div>
      <div class="stat-lbl">минимум (мес)</div>
    </div>
    <div class="card stat-box" style="flex:1;min-width:90px">
      <div class="stat-num" style="color:var(--amber)">${{st.max}}</div>
      <div class="stat-lbl">максимум (мес)</div>
    </div>
    <div class="card stat-box" style="flex:1;min-width:90px">
      <div class="stat-num">${{st.p25}}–${{st.p75}}</div>
      <div class="stat-lbl">P25–P75 (мес)</div>
    </div>
  `;
}}

function binData(entries) {{
  const bins = [0,3,6,9,12,18,24,36,60,120,999];
  const labels = ['0-3','3-6','6-9','9-12','12-18','18-24','24-36','36-60','60-120','120+'];
  const counts = new Array(labels.length).fill(0);
  entries.forEach(e => {{
    for (let i=0; i<bins.length-1; i++) {{
      if (e.months >= bins[i] && e.months < bins[i+1]) {{ counts[i]++; break; }}
    }}
  }});
  return {{labels, counts}};
}}

function renderHist() {{
  const div_info = TIME_DATA[curDiv];
  const color = div_info ? div_info.color : '#4361ee';
  const entries = div_info ? (div_info[curRole] || []) : [];
  const {{labels, counts}} = binData(entries);
  const ctx = document.getElementById('histChart').getContext('2d');
  if (histChart) histChart.destroy();
  histChart = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels, datasets: [{{ data: counts, backgroundColor: color+'aa', borderRadius: 4 }}] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins: {{ legend: {{display:false}} }},
      scales: {{
        x: {{ ticks:{{color:'#8b949e'}}, grid:{{color:'#21262d'}} }},
        y: {{ ticks:{{color:'#8b949e'}}, grid:{{color:'#21262d'}}, beginAtZero:true }},
      }},
    }},
  }});
}}

function renderCompare() {{
  const div_info = TIME_DATA[curDiv];
  if (!div_info) return;
  const lEntries = div_info.Leader || [];
  const fEntries = div_info.Follower || [];
  const color_l = '#4361ee';
  const color_f = '#f72585';
  const maxBins = 10;
  const {{labels, counts: lc}} = binData(lEntries);
  const {{counts: fc}} = binData(fEntries);
  const ctx = document.getElementById('compareChart').getContext('2d');
  if (cmpChart) cmpChart.destroy();
  cmpChart = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels,
      datasets: [
        {{ label:'Leader', data: lc, backgroundColor: color_l+'aa', borderRadius: 3 }},
        {{ label:'Follower', data: fc, backgroundColor: color_f+'aa', borderRadius: 3 }},
      ],
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins: {{ legend: {{labels:{{color:'#8b949e'}}}} }},
      scales: {{
        x: {{ ticks:{{color:'#8b949e'}}, grid:{{color:'#21262d'}} }},
        y: {{ ticks:{{color:'#8b949e'}}, grid:{{color:'#21262d'}}, beginAtZero:true }},
      }},
    }},
  }});
}}

function makeTimeTable(entries, limit) {{
  const show = limit ? entries.slice(0, limit) : entries;
  if (!show.length) return '<p style="color:var(--muted);padding:12px">Нет данных</p>';
  let html = `<div style="overflow-x:auto"><table>
    <thead><tr><th>#</th><th>Имя</th><th>Мес.</th>
    <th>Первый ивент</th><th>Дата закрытия</th><th>Ивент закрытия</th></tr></thead><tbody>`;
  show.forEach((e,i) => {{
    const mo = e.months;
    const col = mo<=6 ? 'var(--green)' : mo<=12 ? 'var(--blue)' : mo<=24 ? 'var(--amber)' : 'var(--red)';
    html += `<tr>
      <td>${{i+1}}</td>
      <td style="font-weight:600">${{e.name}}</td>
      <td><span style="color:${{col}};font-weight:700;font-size:1.05rem">${{mo}}</span></td>
      <td style="color:var(--muted);font-size:.82rem">${{e.first_date}} · ${{e.first_ev}}</td>
      <td style="color:var(--muted);font-size:.82rem">${{e.close_date}}</td>
      <td style="color:var(--muted);font-size:.82rem">${{e.close_ev}}</td>
    </tr>`;
  }});
  html += '</tbody></table></div>';
  return html;
}}

function renderAll() {{
  renderStats();
  renderHist();
  renderCompare();
  const div_info = TIME_DATA[curDiv];
  const entries = div_info ? (div_info[curRole] || []) : [];
  document.getElementById('fastTable').innerHTML = makeTimeTable(entries, 15);
  document.getElementById('allTable').innerHTML = makeTimeTable(entries, 0);
}}
</script>
"""
    return _page("Время в дивизионе", body, "../charts/time_in_division.html")


# ──────────────────────────────────────────────────────────────────────────────
# Дашборд 3: Скорость + воронка
# ──────────────────────────────────────────────────────────────────────────────
def build_speed_dashboard(div_rows: List[Dict]) -> str:
    # Воронка
    funnel: Dict[str, Dict[str, int]] = {}
    for div in DIVISION_ORDER:
        funnel[div] = {"Leader": 0, "Follower": 0}

    for r in div_rows:
        div, role = r["division"], r["role"]
        if div in funnel and role in funnel[div]:
            funnel[div][role] += 1

    funnel_js = {
        "divs":     [d for d in DIVISION_ORDER if funnel[d]["Leader"] or funnel[d]["Follower"]],
        "leaders":  [funnel[d]["Leader"]   for d in DIVISION_ORDER if funnel[d]["Leader"] or funnel[d]["Follower"]],
        "followers":[funnel[d]["Follower"] for d in DIVISION_ORDER if funnel[d]["Leader"] or funnel[d]["Follower"]],
        "colors":   [DIVISION_COLORS[d]    for d in DIVISION_ORDER if funnel[d]["Leader"] or funnel[d]["Follower"]],
    }

    # Скорость (pts/month, минимум 3 месяца активности)
    speed_data: Dict[str, Dict[str, List]] = {}
    for div in DIVISION_ORDER:
        speed_data[div] = {"Leader": [], "Follower": []}

    for r in div_rows:
        if r["speed"] is None or r["months"] is None or r["months"] < 3:
            continue
        div, role = r["division"], r["role"]
        if div in speed_data and role in speed_data[div]:
            speed_data[div][role].append({
                "name":   r["name"],
                "wsdc_id": r["wsdc_id"],
                "pts":    r["points"],
                "months": r["months"],
                "speed":  r["speed"],
                "events": r["events"],
            })

    for div in speed_data:
        for role in speed_data[div]:
            speed_data[div][role].sort(key=lambda x: -x["speed"])

    body = f"""
<a href="../index.html" class="back-link">← Главная</a>
<div class="page-header">
  <h1>⚡ Скорость набора очков и воронка</h1>
  <p>Кто набирает быстрее, сколько людей в каждом дивизионе · {today_str()}</p>
</div>

<div class="card mb32">
  <h3 class="section-title">📐 Воронка дивизионов — Leaders vs Followers</h3>
  <div class="canvas-wrap" style="height:280px;"><canvas id="funnelChart"></canvas></div>
</div>

<div class="card mb32">
  <h3 class="section-title">⚡ Скорость набора очков (pts/месяц)</h3>
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px;">
    <div class="tab-bar" id="speedTabs">
      {''.join(f'<button class="tab-btn" data-div="{d}" onclick="switchSpeedDiv(this)">{d}</button>'
               for d in DIVISION_ORDER if speed_data.get(d, {}).get("Leader") or speed_data.get(d, {}).get("Follower"))}
    </div>
    <div style="display:flex;gap:8px;">
      <button class="role-btn active" id="sBtnL" onclick="switchSpeedRole(\'Leader\')">Leader</button>
      <button class="role-btn" id="sBtnF" onclick="switchSpeedRole(\'Follower\')">Follower</button>
    </div>
  </div>
  <div class="canvas-wrap mb20"><canvas id="speedChart"></canvas></div>
  <div id="speedTable"></div>
</div>

<script>
const FUNNEL = {jd(funnel_js)};
const SPEED = {jd(speed_data)};
let sDiv = null, sRole = 'Leader';
let speedChart = null;

// ── Воронка
new Chart(document.getElementById('funnelChart').getContext('2d'), {{
  type: 'bar',
  data: {{
    labels: FUNNEL.divs,
    datasets: [
      {{ label:'Leader',   data: FUNNEL.leaders,   backgroundColor:'#4361eecc', borderRadius:4 }},
      {{ label:'Follower', data: FUNNEL.followers,  backgroundColor:'#f72585cc', borderRadius:4 }},
    ],
  }},
  options: {{
    responsive:true, maintainAspectRatio:false,
    plugins: {{ legend: {{labels:{{color:'#8b949e'}}}} }},
    scales: {{
      x: {{ticks:{{color:'#8b949e'}}, grid:{{color:'#21262d'}}}},
      y: {{ticks:{{color:'#8b949e'}}, grid:{{color:'#21262d'}}, beginAtZero:true}},
    }},
  }},
}});

// ── Скорость
window.addEventListener('load', () => {{
  const tabs = document.querySelectorAll('.tab-btn');
  if (tabs.length) {{
    sDiv = tabs[0].dataset.div;
    tabs[0].classList.add('active');
  }}
  renderSpeed();
}});

function switchSpeedDiv(btn) {{
  document.querySelectorAll('#speedTabs .tab-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  sDiv = btn.dataset.div;
  renderSpeed();
}}
function switchSpeedRole(r) {{
  sRole = r;
  document.getElementById('sBtnL').classList.toggle('active', r==='Leader');
  document.getElementById('sBtnF').classList.toggle('active', r==='Follower');
  renderSpeed();
}}

function renderSpeed() {{
  const rows = (SPEED[sDiv] && SPEED[sDiv][sRole]) || [];
  const color = '#4361ee';
  const top = rows.slice(0, 30);
  const ctx = document.getElementById('speedChart').getContext('2d');
  if (speedChart) speedChart.destroy();
  speedChart = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: top.map(r=>r.name),
      datasets: [{{
        data: top.map(r=>r.speed),
        backgroundColor: top.map(r => r.speed >= 2 ? '#2dc65399' : r.speed >= 1 ? '#4361eeaa' : '#8b949e55'),
        borderRadius: 4,
      }}],
    }},
    options: {{
      responsive:true, maintainAspectRatio:false, indexAxis:'y',
      plugins: {{ legend:{{display:false}},
        tooltip: {{callbacks: {{label: c => ' ' + c.parsed.x + ' pts/мес'}}}} }},
      scales: {{
        x: {{ticks:{{color:'#8b949e'}}, grid:{{color:'#21262d'}}, beginAtZero:true}},
        y: {{ticks:{{color:'#8b949e',font:{{size:11}}}}, grid:{{display:false}}}},
      }},
    }},
  }});

  let html = `<div style="overflow-x:auto"><table>
    <thead><tr><th>#</th><th>Имя</th><th>Pts/мес</th><th>Всего pts</th>
    <th>Мес. активности</th><th>Ивентов</th></tr></thead><tbody>`;
  rows.forEach((r,i)=>{{
    const col = r.speed>=2?'var(--green)':r.speed>=1?'var(--blue)':'var(--muted)';
    html+=`<tr>
      <td>${{i+1}}</td><td style="font-weight:600">${{r.name}}</td>
      <td><span style="color:${{col}};font-weight:700">${{r.speed}}</span></td>
      <td class="pts">${{r.pts}}</td>
      <td style="color:var(--muted)">${{r.months}}</td>
      <td style="color:var(--muted)">${{r.events}}</td>
    </tr>`;
  }});
  html += '</tbody></table></div>';
  if (!rows.length) html = '<p style="color:var(--muted);padding:16px">Нет данных (нужно ≥3 месяцев активности)</p>';
  document.getElementById('speedTable').innerHTML = html;
}}
</script>
"""
    return _page("Скорость и воронка", body, "../charts/speed_and_funnel.html")


# ──────────────────────────────────────────────────────────────────────────────
# Дашборд 4: Топ мест на турнирах
# ──────────────────────────────────────────────────────────────────────────────
def build_tournament_dashboard(event_rows: List[Dict], div_rows: List[Dict]) -> str:
    # Обогащаем wsdc_id → дивизион (берём «максимальный» по иерархии)
    div_order_idx = {d: i for i, d in enumerate(DIVISION_ORDER)}
    dancer_div: Dict[str, str] = {}
    for r in div_rows:
        wid = r["wsdc_id"]
        if wid not in dancer_div:
            dancer_div[wid] = r["division"]
        else:
            cur_idx = div_order_idx.get(dancer_div[wid], 0)
            new_idx = div_order_idx.get(r["division"], 0)
            if new_idx > cur_idx:
                dancer_div[wid] = r["division"]

    # Топ-3 места по event_tag × contest_name
    podium_rows = [r for r in event_rows if 1 <= r["rank"] <= 3 and r["wsdc_id"]]

    # Список уникальных ивентов
    events = sorted(set(r["event_name"] for r in event_rows if r["event_name"]))
    # Список дивизионов (contest_name → division hint)
    contests = sorted(set(r["contest_name"] for r in event_rows if r["contest_name"]))

    js_rows = []
    for r in podium_rows:
        js_rows.append({
            "rank":       r["rank"],
            "name":       r["name"],
            "wsdc_id":    r["wsdc_id"],
            "role":       r["role"],
            "event":      r["event_name"],
            "contest":    r["contest_name"],
            "div_guess":  dancer_div.get(r["wsdc_id"], "—"),
        })

    body = f"""
<a href="../index.html" class="back-link">← Главная</a>
<div class="page-header">
  <h1>🏆 Топ мест на турнирах</h1>
  <p>Места 1–3 в финалах на участвующих ивентах · {today_str()}</p>
  <div class="meta">Источник: danceConvention API · Только финальные раунды</div>
</div>

<div class="card mb32">
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;align-items:flex-end;">
    <div>
      <div style="font-size:.75rem;color:var(--muted);margin-bottom:4px;">Турнир</div>
      <select id="filterEvent" onchange="renderAll()"
              style="background:var(--card);border:1px solid var(--border);color:var(--text);
                     padding:7px 12px;border-radius:8px;font-size:.83rem;min-width:220px;">
        <option value="">Все турниры</option>
        {''.join(f'<option>{e}</option>' for e in events)}
      </select>
    </div>
    <div>
      <div style="font-size:.75rem;color:var(--muted);margin-bottom:4px;">Дивизион конкурса</div>
      <select id="filterContest" onchange="renderAll()"
              style="background:var(--card);border:1px solid var(--border);color:var(--text);
                     padding:7px 12px;border-radius:8px;font-size:.83rem;min-width:200px;">
        <option value="">Все конкурсы</option>
        {''.join(f'<option>{c}</option>' for c in contests)}
      </select>
    </div>
    <div>
      <div style="font-size:.75rem;color:var(--muted);margin-bottom:4px;">Роль</div>
      <select id="filterRole" onchange="renderAll()"
              style="background:var(--card);border:1px solid var(--border);color:var(--text);
                     padding:7px 12px;border-radius:8px;font-size:.83rem;">
        <option value="">Обе</option>
        <option>Leader</option>
        <option>Follower</option>
      </select>
    </div>
    <div>
      <input class="search-box" id="searchBox" placeholder="Поиск по имени…"
             oninput="renderAll()" style="width:200px;margin:0;margin-top:auto;">
    </div>
  </div>

  <div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:24px;" id="statsRow"></div>

  <div class="canvas-wrap mb20" style="height:300px;"><canvas id="podiumChart"></canvas></div>

  <div id="tableWrap"></div>
</div>

<script>
const ROWS = {jd(js_rows)};

function getFiltered() {{
  const ev = document.getElementById('filterEvent').value;
  const co = document.getElementById('filterContest').value;
  const ro = document.getElementById('filterRole').value;
  const q  = (document.getElementById('searchBox').value||'').toLowerCase();
  return ROWS.filter(r =>
    (!ev || r.event === ev) &&
    (!co || r.contest === co) &&
    (!ro || r.role === ro) &&
    (!q  || r.name.toLowerCase().includes(q))
  );
}}

function renderAll() {{
  const rows = getFiltered();

  // Stats
  const gold = rows.filter(r=>r.rank===1).length;
  const silver = rows.filter(r=>r.rank===2).length;
  const bronze = rows.filter(r=>r.rank===3).length;
  const unique = new Set(rows.map(r=>r.wsdc_id)).size;
  document.getElementById('statsRow').innerHTML = `
    <div class="card stat-box" style="flex:1;min-width:80px">
      <div class="stat-num gold">🥇 ${{gold}}</div><div class="stat-lbl">первых мест</div></div>
    <div class="card stat-box" style="flex:1;min-width:80px">
      <div class="stat-num silver">🥈 ${{silver}}</div><div class="stat-lbl">вторых мест</div></div>
    <div class="card stat-box" style="flex:1;min-width:80px">
      <div class="stat-num bronze">🥉 ${{bronze}}</div><div class="stat-lbl">третьих мест</div></div>
    <div class="card stat-box" style="flex:1;min-width:80px">
      <div class="stat-num" style="color:var(--blue)">${{unique}}</div><div class="stat-lbl">уникальных танцоров</div></div>
  `;

  // Chart: кто сколько подиумов
  const countMap = {{}};
  rows.forEach(r => {{ countMap[r.name] = (countMap[r.name]||0) + 1; }});
  const sorted = Object.entries(countMap).sort((a,b)=>b[1]-a[1]).slice(0,20);
  const ctx = document.getElementById('podiumChart').getContext('2d');
  if (window._pc) window._pc.destroy();
  window._pc = new Chart(ctx, {{
    type: 'bar', indexAxis: 'y',
    data: {{
      labels: sorted.map(x=>x[0]),
      datasets: [{{ data: sorted.map(x=>x[1]),
        backgroundColor: sorted.map((_,i) => i===0?'#f6d36599':i===1?'#c0c0c099':'#cd7f3299'),
        borderRadius: 4 }}],
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>' '+c.parsed.x+' подиумов'}}}} }},
      scales: {{
        x: {{ticks:{{color:'#8b949e'}}, grid:{{color:'#21262d'}}, beginAtZero:true}},
        y: {{ticks:{{color:'#8b949e',font:{{size:11}}}}, grid:{{display:false}}}},
      }},
    }},
  }});

  // Table
  const medal = {{1:'🥇',2:'🥈',3:'🥉'}};
  let html = `<div style="overflow-x:auto"><table>
    <thead><tr><th>Место</th><th>Имя</th><th>Роль</th><th>Конкурс</th>
    <th>Турнир</th><th>Дивизион (реестр)</th><th>WSDC ID</th></tr></thead><tbody>`;
  rows.forEach(r=>{{
    html+=`<tr>
      <td><span class="rank-medal">${{medal[r.rank]||r.rank}}</span></td>
      <td style="font-weight:600">${{r.name}}</td>
      <td style="color:var(--muted)">${{r.role}}</td>
      <td>${{r.contest}}</td>
      <td style="color:var(--muted);font-size:.82rem">${{r.event}}</td>
      <td><span class="badge" style="background:rgba(67,97,238,.15);color:#7ba7ff">${{r.div_guess}}</span></td>
      <td><a href="https://points.worldsdc.com/lookup2020?q=${{r.wsdc_id}}" target="_blank"
             style="color:var(--muted);font-size:.8rem">${{r.wsdc_id}}</a></td>
    </tr>`;
  }});
  html += '</tbody></table></div>';
  if (!rows.length) html = '<p style="color:var(--muted);padding:20px">Нет данных по фильтрам</p>';
  document.getElementById('tableWrap').innerHTML = html;
}}

window.onload = renderAll;
</script>
"""
    return _page("Топ мест на турнирах", body, "../charts/tournament_results.html")


# ──────────────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--divisions-csv",  default="wsdc_registry_divisions_from_dc_export.csv")
    ap.add_argument("--placements-csv", default="wsdc_registry_placements_from_dc_export.csv")
    ap.add_argument("--events-csv",     default="dc_wsdc_events_export.csv")
    ap.add_argument("--out-dir",        default="charts")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    print("Zaghruzhayu dannye...")
    div_rows    = load_divisions(args.divisions_csv)
    rating_rows = build_rating_rows(div_rows)
    rating_rows = add_zero_point_rows_from_events(
        rating_rows, args.events_csv, div_rows
    )
    placements  = load_placements(args.placements_csv)
    event_rows  = load_events(args.events_csv)
    print(
        f"  divisions={len(div_rows)} (rating rows: {len(rating_rows)}), "
        f"placements={len(placements)}, events={len(event_rows)}"
    )

    pages = [
        ("rating_dashboard.html",    build_rating_dashboard(rating_rows)),
        ("time_in_division.html",    build_time_dashboard(div_rows, placements)),
        ("speed_and_funnel.html",    build_speed_dashboard(div_rows)),
        ("tournament_results.html",  build_tournament_dashboard(event_rows, div_rows)),
    ]

    for fname, html in pages:
        path = os.path.join(args.out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  OK {path}")

    print("Готово.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
