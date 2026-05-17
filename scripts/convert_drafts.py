#!/usr/bin/env python3
"""
Convert markdown drafts from ~/dads-blog/content/drafts/ to Astro content collection
at ~/migukstory/src/content/blog/[slug].md with proper frontmatter.

Handles:
- Extract title (# heading)
- Extract meta description from "**메타 설명:**" line
- Extract labels from "**라벨(태그):**" line
- Strip the labels/meta/sources footer
- Detect age group from filename keywords
- Convert Mermaid code blocks (Astro renders ```mermaid natively via MDX or we use a remark plugin)
- Add proper frontmatter

Usage:
  python3 convert_drafts.py
"""

import re
import sys
from datetime import datetime
from pathlib import Path

DRAFTS = Path.home() / "dads-blog" / "content" / "drafts"
DEST = Path.home() / "migukstory" / "src" / "content" / "blog"

# Files to skip (test/old drafts not for migukstory)
SKIP = {
    "20260517-0001_sample-test.md",
    "auto_20260517-003423_60대가_꼭_알아야_할_월_100만원_만드는_노후재테크_5가지.md",
    "auto_20260517-003439_은퇴_후_생활비_부족할_때_실제로_도움되는_재테크_방법_추천.md",
    "auto_20260517-003455_연금만으로_부족한_노후자금__안전하게_모으는_비법_3가지.md",
}

# Slug overrides for files with non-English names
SLUG_OVERRIDES = {
    "h1b_100k_korean_students": "h1b-100k-korean-students",
    "trump_account_1000_newborn": "trump-account-1000-newborn",
}


def detect_age_group(slug: str, content: str) -> str:
    s = slug.lower() + " " + content.lower()
    if any(k in s for k in ["medicare", "social-security", "senior", "elderly",
                              "65세", "은퇴", "양로", "치매", "memory", "totalization", "pension"]):
        return "55+"
    if any(k in s for k in ["college-admission", "salt", "i130", "school-district",
                             "homeowner", "401k", "mortgage", "parents-2026", "i-130"]):
        return "35-55"
    if any(k in s for k in ["h1b", "h-1b", "f1", "opt", "stem", "credit-score",
                             "student", "korean-students", "유학생"]):
        return "20-35"
    return "all"


def parse_draft(path: Path) -> dict:
    md = path.read_text(encoding="utf-8")
    lines = md.split("\n")

    # Title from first # heading
    title = "Untitled"
    body_start = 0
    for i, line in enumerate(lines):
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            title = m.group(1).strip()
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()

    # Meta description
    desc = ""
    m = re.search(r"\*\*메타 설명:\*\*\s*(.+?)(?:\n|$)", md)
    if m:
        desc = m.group(1).strip()
    else:
        # Fallback: first 150 chars of body
        clean = re.sub(r"```mermaid.*?```", "", body, flags=re.DOTALL)
        clean = re.sub(r"[#*\n]+", " ", clean).strip()
        desc = clean[:155]

    # Labels/tags
    tags = []
    m = re.search(r"\*\*라벨\(태그\):\*\*\s*(.+?)(?:\n|$)", md)
    if m:
        tags = [s.strip() for s in m.group(1).split(",") if s.strip()]

    # Strip footer (sources, labels, meta)
    body_clean = re.sub(
        r"\n---\s*\n\*\*(출처|라벨|메타).*$",
        "",
        body,
        flags=re.DOTALL,
    ).strip()

    # Determine slug
    stem = path.stem
    slug = SLUG_OVERRIDES.get(stem, stem)
    # Sanitize: lowercase, no special chars except hyphen
    slug = re.sub(r"[^a-z0-9-]", "-", slug.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")

    age = detect_age_group(slug, body)

    return {
        "title": title,
        "description": desc,
        "tags": tags,
        "ageGroup": age,
        "slug": slug,
        "body": body_clean,
    }


def write_astro_md(post: dict, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / f"{post['slug']}.md"

    # Escape single quotes in YAML string values
    title_esc = post["title"].replace("'", "''")
    desc_esc = post["description"].replace("'", "''")

    tags_yaml = "[" + ", ".join(f"'{t}'" for t in post["tags"]) + "]"

    frontmatter = (
        "---\n"
        f"title: '{title_esc}'\n"
        f"description: '{desc_esc}'\n"
        f"pubDate: '2026-05-17'\n"
        f"tags: {tags_yaml}\n"
        f"ageGroup: '{post['ageGroup']}'\n"
        "---\n\n"
    )

    out.write_text(frontmatter + post["body"] + "\n", encoding="utf-8")
    return out


def main():
    if not DRAFTS.exists():
        print(f"❌ Drafts folder not found: {DRAFTS}")
        sys.exit(1)

    DEST.mkdir(parents=True, exist_ok=True)

    converted = 0
    for path in sorted(DRAFTS.glob("*.md")):
        if path.name in SKIP:
            print(f"⏭️  Skip: {path.name}")
            continue

        try:
            post = parse_draft(path)
            out = write_astro_md(post, DEST)
            print(f"✅ {post['slug']:50s} → age:{post['ageGroup']:6s} tags:{len(post['tags'])}")
            converted += 1
        except Exception as e:
            print(f"❌ {path.name}: {e}")

    print(f"\n🏁 Converted {converted} drafts → {DEST}")


if __name__ == "__main__":
    main()
