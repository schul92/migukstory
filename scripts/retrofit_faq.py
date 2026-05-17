#!/usr/bin/env python3
"""
Retrofit FAQ frontmatter onto existing posts in src/content/blog/.

Parses each post's "## 자주 묻는 질문 (FAQ)" section, extracts Q/A pairs,
and inserts them as YAML `faq:` block in the frontmatter (if not already present).

Triggers FAQPage JSON-LD emission via the BlogPost layout / BaseHead schema pipeline.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BLOG = REPO / "src" / "content" / "blog"

FAQ_HEADING = re.compile(r"^##+\s*(자주\s*묻는\s*질문|FAQ)", re.MULTILINE)
QA_PATTERN = re.compile(
    r"\*\*Q\d*\.\s*(.+?)\*\*\s*\n+(?:A\.\s*)?(.+?)(?=\n\n\*\*Q\d*\.|\n\n##|\Z)",
    re.DOTALL,
)


def yaml_escape(s: str) -> str:
    s = s.strip()
    # Replace problematic chars; use double-quoted YAML
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = re.sub(r"\s+", " ", s)
    return s


def extract_faq(body: str):
    m = FAQ_HEADING.search(body)
    if not m:
        return []
    after = body[m.end():]
    # Cut at next H2 (so we don't bleed into "## 마무리" etc.)
    next_h2 = re.search(r"\n##\s+", after)
    if next_h2:
        after = after[:next_h2.start()]
    pairs = []
    for q, a in QA_PATTERN.findall(after):
        # Strip leading markdown bullet/bold artifacts from answer
        a_clean = re.sub(r"^\*+\s*", "", a.strip())
        # Cap answer at ~280 chars for schema (Google rich-results best practice)
        a_clean = re.sub(r"\s+", " ", a_clean).strip()
        if len(a_clean) > 320:
            a_clean = a_clean[:317].rstrip() + "..."
        pairs.append((yaml_escape(q), yaml_escape(a_clean)))
    return pairs


def has_faq_frontmatter(frontmatter: str) -> bool:
    return bool(re.search(r"^faq:", frontmatter, re.MULTILINE))


def insert_faq(text: str, pairs):
    # Split frontmatter
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    _, fm, body = parts
    if has_faq_frontmatter(fm):
        return None  # already retrofitted

    faq_yaml = "faq:\n"
    for q, a in pairs:
        faq_yaml += f'  - q: "{q}"\n'
        faq_yaml += f'    a: "{a}"\n'

    # Insert before closing of frontmatter
    new_fm = fm.rstrip() + "\n" + faq_yaml
    return f"---{new_fm}---{body}"


def main():
    if not BLOG.exists():
        print(f"⚠️ {BLOG} not found", file=sys.stderr)
        sys.exit(1)

    updated = 0
    skipped = 0
    no_faq = 0
    for md in sorted(BLOG.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        pairs = extract_faq(text)
        if not pairs:
            no_faq += 1
            continue
        new_text = insert_faq(text, pairs)
        if new_text is None:
            skipped += 1
            continue
        md.write_text(new_text, encoding="utf-8")
        print(f"✅ {md.name}: {len(pairs)} FAQ pairs")
        updated += 1

    print()
    print(f"📊 Updated: {updated} · Skipped (already has FAQ): {skipped} · No FAQ section: {no_faq}")


if __name__ == "__main__":
    main()
