#!/usr/bin/env python3
"""Проверка постов на AI-паттерны (002_AI_ПАТТЕРНЫ.txt + СТИЛЬ-гайды канала).

Ловит маркеры машинного текста:
  - длинное тире «—» (запрещено полностью, ноль на статью);
  - избыток средних тире «–» (норма: только диапазоны, максимум 3 на статью);
  - канцелярит, шаблонные конструкции, связки и клише нейросети.

Запускать перед каждым git push (аналогично check_dates.py).
Использование:
    python3 scripts/check_ai_patterns.py            # все посты _posts/*.md
    python3 scripts/check_ai_patterns.py _posts/X.md  # один файл (для агента)
"""
import glob
import re
import sys

EM = "\u2014"  # —
EN = "\u2013"  # –

# Стоп-паттерны нейросети. \bявляется\b НЕ матчит «появляется/проявляется» (нет границы слова).
AI_PATTERNS = [
    r"\bявляется\b",
    r"представляет собой",
    r"осуществл\w*",
    r"\bданн(ый|ая|ое|ого|ому|ым|ой|ыми|ую)\b",
    r"\bв целях\b",
    r"играет важную роль",
    r"способствует развитию",
    r"давайте рассмотрим",
    r"важно понимать",
    r"но есть нюанс",
    r"\bименно поэтому\b",
    r"\bпосле этого\b",
    r"начать стоит с",
    r"во многих странах",
    r"следите за обновлениями",
    r"по всему миру",
    r"в последние годы",
    r"\bнезависимо от\b",
    r"вышеуказанн\w*",
    r"вышеописанн\w*",
    r"\bследует отметить\b",
    r"\bстоит отметить\b",
    r"в данной статье",
    r"в этой статье",
]
AI_RE = re.compile("|".join(AI_PATTERNS), re.IGNORECASE)

EN_MAX = 3  # максимум средних тире на статью (диапазоны)


def check_file(path):
    """Возвращает список проблем по файлу."""
    text = open(path, encoding="utf-8", errors="ignore").read()
    problems = []

    em = text.count(EM)
    if em:
        lines = [i + 1 for i, ln in enumerate(text.splitlines()) if EM in ln]
        problems.append(f"{em} длинных тире (—), строки: {lines[:10]}{' …' if len(lines) > 10 else ''}")

    en = text.count(EN)
    if en > EN_MAX:
        problems.append(f"{en} средних тире (–), допустимо ≤ {EN_MAX} (только диапазоны)")

    hits = AI_RE.findall(text)
    if hits:
        found = {}
        for m in AI_RE.finditer(text):
            key = m.group(0).lower()
            found[key] = found.get(key, 0) + 1
        problems.append("AI-слова: " + ", ".join(f"{k}×{v}" for k, v in sorted(found.items())))

    return problems


def main():
    files = sys.argv[1:] or sorted(glob.glob("_posts/*.md"))
    bad = 0
    for f in files:
        problems = check_file(f)
        if problems:
            bad += 1
            print(f"  {f}")
            for p in problems:
                print(f"      • {p}")

    if bad:
        print(f"\nОШИБКА: {bad} из {len(files)} файлов содержат AI-паттерны.")
        raise SystemExit(1)

    print(f"OK: {len(files)} файлов без AI-паттернов (нет длинных тире, средних ≤ {EN_MAX}, стоп-слов нет).")


if __name__ == "__main__":
    main()
