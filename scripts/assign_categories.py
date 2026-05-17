#!/usr/bin/env python3
"""
Bulk-add `category:` to existing post frontmatter based on filename keywords.
Maps each post to one of 7 standard Korean news categories.
"""
import re
from pathlib import Path

BLOG = Path.home() / "migukstory" / "src" / "content" / "blog"

# Filename → category mapping (longest match first)
RULES = [
    ("h1b",                       "immigration"),
    ("f1-opt",                    "immigration"),
    ("opt-stem",                  "immigration"),
    ("birthright-citizenship",    "immigration"),
    ("citizenship-test",          "immigration"),
    ("i130",                      "immigration"),
    ("salt",                      "tax"),
    ("obbba",                     "tax"),
    ("trump-account",             "tax"),
    ("credit-score",              "tax"),
    ("totalization",              "retirement"),
    ("medicare",                  "health"),
    ("voice-clone-scam",          "health"),  # senior safety/health adjacent
    ("ai-voice",                  "health"),
    ("school-districts",          "education"),
    ("college-admission",         "education"),
    ("carrollton",                "community"),
    ("koreatown-shooting",        "community"),
    ("maggie-kang",               "community"),
    ("oscar",                     "community"),
    ("hyundai",                   "community"),
]

def detect_category(stem: str) -> str:
    s = stem.lower()
    for keyword, cat in RULES:
        if keyword in s:
            return cat
    return "community"  # fallback


def main():
    updated = 0
    for path in sorted(BLOG.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            print(f"⏭️  {path.name} — no frontmatter, skipping")
            continue

        # Skip if category already present
        if re.search(r"^category:", content, re.MULTILINE):
            print(f"✓  {path.name} — already has category")
            continue

        category = detect_category(path.stem)

        # Insert category line right after ageGroup line (or before closing ---)
        if re.search(r"^ageGroup:", content, re.MULTILINE):
            new_content = re.sub(
                r"(^ageGroup:.*$)",
                f"\\1\ncategory: '{category}'",
                content,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            # Insert before closing ---
            lines = content.split("\n")
            # find frontmatter end (second ---)
            end_idx = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    end_idx = i
                    break
            if end_idx:
                lines.insert(end_idx, f"category: '{category}'")
                new_content = "\n".join(lines)
            else:
                print(f"❌ {path.name} — couldn't find frontmatter end")
                continue

        path.write_text(new_content, encoding="utf-8")
        print(f"✅ {path.name:55s} → {category}")
        updated += 1

    print(f"\n🏁 Updated {updated} posts")


if __name__ == "__main__":
    main()
