#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Небольшой утилитарный скрипт для поиска API-эндпоинтов WSDC Points Registry.

Задача: скачать HTML/JS с https://points.worldsdc.com/lookup2020 и найти строки вида
  /api/...
чтобы понять, откуда берутся поинты без Playwright.

Запуск:
  python discover_wsdc_endpoints.py
"""

from __future__ import annotations

import re
import sys
from urllib.parse import urljoin

import requests


LOOKUP_URL = "https://points.worldsdc.com/lookup2020"


def main() -> int:
    s = requests.Session()
    s.trust_env = False  # не используем HTTP(S)_PROXY из окружения

    html = s.get(LOOKUP_URL, timeout=30).text
    print(f"HTML length: {len(html)}")

    script_srcs = re.findall(r"<script[^>]+src=['\\\"]([^'\\\"]+)['\\\"]", html, flags=re.IGNORECASE)
    script_urls = [urljoin(LOOKUP_URL, u) for u in script_srcs]
    print(f"Scripts found: {len(script_urls)}")
    for u in script_urls[:30]:
        print("  ", u)

    api_hits = set(re.findall(r"/api/[^'\"\\s<>]+", html))
    print(f"API hits in HTML: {len(api_hits)}")
    for h in sorted(api_hits)[:50]:
        print("  ", h)

    # Сканируем JS файлы на /api/
    for u in script_urls:
        try:
            js = s.get(u, timeout=30).text
            print(f"\n=== Analyzing {u} ({len(js)} bytes) ===")
        except Exception as e:
            print(f"[warn] failed to fetch {u}: {e}")
            continue

        # Ищем API эндпоинты
        api_hits = set(re.findall(r"/api/[^'\"\\s<>]+", js))
        if api_hits:
            print(f"API endpoints found: {len(api_hits)}")
            for h in sorted(api_hits):
                print("  ", h)

        # Ищем URL-паттерны с 'points', 'lookup', 'dancer'
        url_patterns = re.findall(r"['\"](https?://[^'\"]+/(?:api|points|lookup|dancer)[^'\"]*)['\"]", js, re.IGNORECASE)
        if url_patterns:
            print(f"URL patterns found: {len(url_patterns)}")
            for p in sorted(set(url_patterns))[:50]:
                print("  ", p)

        # Ищем вызовы fetch/ajax/get/post с URL
        fetch_calls = re.findall(r"(?:fetch|ajax|\.get|\.post)\s*\(['\"]([^'\"]+)['\"]", js, re.IGNORECASE)
        if fetch_calls:
            print(f"Fetch/AJAX calls found: {len(fetch_calls)}")
            for f in sorted(set(fetch_calls))[:50]:
                if '/api' in f or '/points' in f or '/lookup' in f:
                    print("  ", f)

        # Ищем упоминания wsdc_id и как они используются
        wsdc_id_usage = re.findall(r"wsdc[_-]?id[^'\"\\s<>]*['\"]?\s*[:=]\s*['\"]?([^'\"\\s<>]+)", js, re.IGNORECASE)
        if wsdc_id_usage:
            print(f"WSDC ID usage patterns: {len(wsdc_id_usage)}")
            for w in sorted(set(wsdc_id_usage))[:20]:
                print("  ", w)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

