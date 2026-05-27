"""SEO checker for Jekyll static site."""
import os
import re
import sys

SITE_DIR = "_site"
errors = []


def check_file(filepath):
    relpath = os.path.relpath(filepath, SITE_DIR)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Skip non-HTML files
    if not content.strip().startswith("<!DOCTYPE html") and not content.strip().startswith("<html"):
        return

    # 1. Title tag
    title_match = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
    if not title_match:
        errors.append(f"{relpath}: MISSING <title>")
    elif not title_match.group(1).strip():
        errors.append(f"{relpath}: EMPTY <title>")

    # 2. Meta description
    desc_match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
        content,
    )
    if not desc_match:
        desc_match = re.search(
            r'<meta\s+content=["\']([^"\']*)["\']\s+name=["\']description["\']',
            content,
        )
    if not desc_match:
        errors.append(f"{relpath}: MISSING meta description")
    elif not desc_match.group(1).strip():
        errors.append(f"{relpath}: EMPTY meta description")

    # 3. Canonical URL
    if 'rel="canonical"' not in content and "rel=canonical" not in content:
        errors.append(f"{relpath}: MISSING canonical URL")

    # 4. Open Graph tags
    if 'property="og:title"' not in content and 'property="og:description"' not in content:
        errors.append(f"{relpath}: MISSING Open Graph tags")

    # 5. Viewport meta tag
    if 'name="viewport"' not in content:
        errors.append(f"{relpath}: MISSING viewport meta tag")

    # 6. h1 tag
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL)
    if not h1_match:
        errors.append(f"{relpath}: MISSING <h1>")

    # 7. Multiple h1 tags
    h1_all = re.findall(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL)
    if len(h1_all) > 1:
        errors.append(f"{relpath}: MULTIPLE <h1> tags ({len(h1_all)} found)")

    # 8. Images without alt text
    imgs = re.findall(r"<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>", content)
    for img in imgs:
        img_tag_match = re.search(
            rf'<img[^>]*src=["\']{re.escape(img)}["\'][^>]*>', content
        )
        if img_tag_match:
            img_tag = img_tag_match.group(0)
            if 'alt=' not in img_tag and 'alt "' not in img_tag:
                errors.append(f"{relpath}: IMG missing alt text: {img[:80]}")

    # 9. JSON-LD structured data
    if 'application/ld+json' not in content:
        errors.append(f"{relpath}: MISSING JSON-LD structured data")

    # 10. Language attribute on html tag
    if 'lang="' not in content[:500] and "lang='" not in content[:500]:
        errors.append(f"{relpath}: MISSING lang attribute on <html>")


def main():
    for root, dirs, files in os.walk(SITE_DIR):
        for fname in files:
            fpath = os.path.join(root, fname)
            if fname.endswith(".html"):
                check_file(fpath)

    if errors:
        print(f"\n{'='*60}")
        print(f"SEO CHECK FAILED — {len(errors)} issue(s) found:")
        print(f"{'='*60}")
        for err in errors:
            print(f"  ✖ {err}")
        print(f"{'='*60}")
        sys.exit(1)
    else:
        print(f"\n{'='*60}")
        print("SEO CHECK PASSED — no issues found.")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
