#!/usr/bin/env python3
"""Проверка front matter постов и страниц.

Ловит класс ошибок, из-за которого посты выпадали из сборки: непарные кавычки
и неэкранированное ': ' внутри title/description ломают YAML, Jekyll перестаёт
видеть front matter и отдаёт пост как статический файл — без заголовка,
описания и по адресу из имени файла.

Запуск: python3 scripts/check_frontmatter.py
"""
import glob
import os
import re
import sys

DATE_RE = re.compile(r"^date:\s*(\d{4}-\d{2}-\d{2})", re.M)
PERMA_RE = re.compile(r"^permalink:\s*(\S+)", re.M)
TITLE_RE = re.compile(r"^title:\s*(.*)$", re.M)
DESC_RE = re.compile(r"^description:\s*(.*)$", re.M)
FIELD_RE = re.compile(r"^([a-z_]+):\s*(.*)$", re.M)
FILENAME_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")

INTENTIONAL_STATIC = {"color_key.html", "yandex_0037927fe0b86a6f.html"}


def quoted_ok(val):
    if val.startswith('"'):
        return bool(re.search(r'(?<!\\)"\s*$', val))
    if val.startswith("'"):
        return bool(re.search(r"(?<!\\)'\s*$", val))
    return True


def main():
    errors = []
    warnings = []
    checked = 0

    posts = sorted(glob.glob("_posts/*.md"))
    pages = sorted(p for p in glob.glob("*.md") + glob.glob("*.html")
                   if os.path.basename(p) != "README.md")

    for path in posts:
        checked += 1
        text = open(path, encoding="utf-8").read()
        if not text.startswith("---") or text.count("---") < 2:
            errors.append(f"{path}: нет front matter — пост не соберётся как страница")
            continue
        fm = text.split("---", 2)[1]

        for m in FIELD_RE.finditer(fm):
            key, val = m.group(1), m.group(2)
            if key not in ("title", "description"):
                continue
            lineno = fm[: m.start()].count("\n") + 2
            if not quoted_ok(val):
                errors.append(f"{path}:{lineno}: {key} — значение в кавычках не закрыто")
            if val and not val.startswith(('"', "'")) and ": " in val:
                errors.append(f"{path}:{lineno}: {key} — неэкранированное ': ' в значении")

        base = os.path.basename(path)[:-3]
        fd = FILENAME_DATE_RE.match(base)
        dm = DATE_RE.search(fm)
        if not TITLE_RE.search(fm):
            errors.append(f"{path}: нет поля title")
        if not DESC_RE.search(fm):
            errors.append(f"{path}: нет поля description")
        if not dm:
            warnings.append(f"{path}: нет поля date — Jekyll возьмёт дату из имени файла ({fd.group(1) if fd else '?'})")
        elif fd and fd.group(1) != dm.group(1):
            errors.append(f"{path}: дата в имени файла ({fd.group(1)}) не совпадает с date ({dm.group(1)})")
        if not PERMA_RE.search(fm):
            warnings.append(f"{path}: нет permalink — адрес будет из имени файла")

    for path in pages:
        name = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        has_fm = text.startswith("---") and text.count("---") >= 2
        if not has_fm:
            checked += 1
            if name in INTENTIONAL_STATIC:
                warnings.append(f"{path}: статический файл без front matter (так задумано)")
            else:
                errors.append(f"{path}: нет front matter — страница не соберётся")
            continue
        checked += 1
        fm = text.split("---", 2)[1]
        for m in FIELD_RE.finditer(fm):
            key, val = m.group(1), m.group(2)
            if key not in ("title", "description"):
                continue
            if not quoted_ok(val):
                errors.append(f"{path}: {key} — значение в кавычках не закрыто")
            if val and not val.startswith(('"', "'")) and ": " in val:
                errors.append(f"{path}: {key} — неэкранированное ': ' в значении")

    print(f"проверено файлов: {checked}")
    print(f"ошибок: {len(errors)}")
    for e in errors:
        print(f"  ОШИБКА   {e}")
    print(f"предупреждений: {len(warnings)}")
    for w in warnings:
        print(f"  ВНИМАНИЕ {w}")
    if errors:
        print("\nПРОВАЛ: эти файлы нельзя пушить.")
        return 1
    print("\nПРОЙДЕНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
