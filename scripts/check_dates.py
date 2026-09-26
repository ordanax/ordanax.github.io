#!/usr/bin/env python3
"""Проверка: нет ли постов с будущей датой публикации.

Причина: в _config.yml стоит `future: false`, Jekyll не публикует посты
с датой позже сегодняшней — статья есть в git, но сайт отдаёт 404.
Запускать перед каждым git push (новые партии).
"""
import glob
import re
from datetime import date

today = date.today()
bad = []

for f in glob.glob('_posts/*.md'):
    m = re.search(r'^date:\s*(\d{4})-(\d{2})-(\d{2})', open(f).read(), re.M)
    if not m:
        continue
    y, mo, d = map(int, m.groups())
    post = date(y, mo, d)
    if post > today:
        bad.append((f, post.isoformat(), today.isoformat()))

if bad:
    print(f"ОШИБКА: {len(bad)} постов с будущей датой (today={today}):")
    for f, post, _ in bad:
        print(f"  {f} -> date {post}")
    raise SystemExit(1)
else:
    print(f"OK: все {len(glob.glob('_posts/*.md'))} постов с датой <= {today}")