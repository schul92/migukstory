#!/usr/bin/env python3
"""
Daily post generator for migukstory.com.

Pops the first topic from scripts/topic_queue.txt, calls Anthropic API
to generate a Korean blog post following the site's editorial format,
writes it to src/content/blog/<slug>.md with proper frontmatter,
and removes the topic from the queue.

Designed to be run via GitHub Actions on a daily cron.

Env vars required:
    ANTHROPIC_API_KEY — Anthropic API key (set as GitHub Secret)

Optional env vars:
    MODEL — anthropic model id (default: claude-sonnet-4-6)
    MAX_POSTS_PER_RUN — int (default: 1)
"""

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

REPO = Path(__file__).resolve().parent.parent
QUEUE = REPO / "scripts" / "topic_queue.txt"
BLOG = REPO / "src" / "content" / "blog"
MODEL = os.environ.get("MODEL", "claude-sonnet-4-6")

PROMPT_TEMPLATE = """당신은 한국 SEO 블로그 작가입니다. 미국에 사는 한국인 독자를 위한 정보 매체 '미국 스토리(Miguk Story)'의 편집 가이드라인을 따라 글을 작성합니다.

**오늘 쓸 글의 주제:** {topic}
**카테고리:** {category}
**참고 출처 힌트:** {source_hint}

**필수 규칙:**
1. 길이: 1,800~2,500 한국어 문자
2. 톤: 정중체 (~입니다, ~네요). 신문 기사 수준의 깔끔한 한국어. AI 티 나는 표현 금지.
3. 모든 사실 주장은 정부 1차 출처(USCIS, IRS, SSA 등) 또는 주요 언론(NYT, NPR, Korea Times, JoongAng) 링크 포함.
4. 가짜 통계, 가짜 인용문, 가짜 출처 절대 금지. 확실하지 않으면 "공식 발표 기준" 같은 헷지 표현 사용.
5. 의학·법률·세무 단정 조언 금지 → "전문가 상담 권장" 한 줄 추가.
6. Mermaid 다이어그램 1개 권장 (프로세스, 비교, 의사결정 트리 등 시각화에 유용한 경우).

**필수 구조:**
```
# [50자 이내 제목 — 검색 키워드 포함]

[3-4줄 도입 — 왜 이 글이 한인 독자에게 유용한지]

## 1. [소제목]
[내용]

## 2. [소제목]
[내용]

```mermaid
flowchart LR
    A[시작] --> B[다음]
    ...
```

## 3. [소제목]
[내용]

## 4. [소제목]
[내용]

## 자주 묻는 질문 (FAQ)
**Q1. [실제 검색 가능한 질문]**
A. [50-80자 답변]

(3-5 Q&A)

## 마무리
[2-3줄 정리 + 독자 질문]

---

**출처(Sources):**
- [Source Name](URL)
- [Source Name](URL)

**라벨(태그):** [쉼표로 5-7개]

**메타 설명:** [120-155자, 핵심 키워드 포함]
```

위 형식을 정확히 따라주세요. 위 구조 외의 부가 설명 없이 마크다운만 출력하세요."""


def slugify(title: str) -> str:
    """Build URL-safe slug from Korean title using transliteration of leading English keywords."""
    # Extract first English-friendly chunk (acronyms, brands, numbers) if present
    eng = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]*", title)
    base = "-".join(eng[:5]).lower() if eng else "post"
    # Add year suffix if a 4-digit year present
    year_m = re.search(r"(20\d{2})", title)
    if year_m and year_m.group(1) not in base:
        base = f"{base}-{year_m.group(1)}"
    # Add date stamp for uniqueness
    today = datetime.now(timezone.utc).strftime("%m%d")
    slug = f"{base}-{today}"[:60]
    return re.sub(r"-+", "-", slug).strip("-")


def parse_queue_line(line: str) -> dict | None:
    """Parse '[category]|[topic]|[source]'. Returns dict or None if invalid/comment."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split("|")
    if len(parts) < 2:
        return None
    return {
        "category": parts[0].strip(),
        "topic": parts[1].strip(),
        "source_hint": parts[2].strip() if len(parts) > 2 else "",
    }


def pop_next_topic() -> tuple[dict | None, list[str]]:
    """Pop the first valid topic; return (topic, remaining_lines)."""
    if not QUEUE.exists():
        return None, []
    lines = QUEUE.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        item = parse_queue_line(line)
        if item:
            new_lines = lines[:i] + lines[i + 1 :]
            return item, new_lines
    return None, lines


def extract_meta(md: str) -> tuple[list[str], str]:
    """Extract labels + meta description from generated post footer."""
    labels: list[str] = []
    desc = ""
    m = re.search(r"\*\*라벨\(태그\):\*\*\s*([^\n]+)", md)
    if m:
        labels = [s.strip() for s in m.group(1).split(",") if s.strip()]
    m2 = re.search(r"\*\*메타 설명:\*\*\s*([^\n]+)", md)
    if m2:
        desc = m2.group(1).strip()
    return labels, desc


def extract_title_and_body(md: str) -> tuple[str, str]:
    """First # heading is title; rest is body. Strip frontmatter footer."""
    body = re.sub(r"\n+\*\*라벨\(태그\):\*\*[^\n]+", "", md)
    body = re.sub(r"\n+\*\*메타 설명:\*\*[^\n]+", "", body)
    body = re.sub(r"\n+---\s*\n*$", "", body).strip()

    title = "Untitled"
    body_start = 0
    for i, line in enumerate(body.split("\n")):
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            title = m.group(1).strip()
            body_start = i + 1
            break
    body_no_title = "\n".join(body.split("\n")[body_start:]).strip()
    return title, body_no_title


def write_post(title: str, body: str, labels: list[str], desc: str,
                category: str, slug: str) -> Path:
    BLOG.mkdir(parents=True, exist_ok=True)
    out = BLOG / f"{slug}.md"

    # Escape single quotes in YAML
    title_esc = title.replace("'", "''")
    desc_esc = desc.replace("'", "''")
    tags_yaml = "[" + ", ".join(f"'{t}'" for t in labels) + "]"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    frontmatter = (
        "---\n"
        f"title: '{title_esc}'\n"
        f"description: '{desc_esc}'\n"
        f"pubDate: '{today}'\n"
        f"tags: {tags_yaml}\n"
        f"category: '{category}'\n"
        f"ageGroup: 'all'\n"
        "---\n\n"
    )
    out.write_text(frontmatter + body + "\n", encoding="utf-8")
    return out


def generate(topic_item: dict) -> str:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = PROMPT_TEMPLATE.format(
        topic=topic_item["topic"],
        category=topic_item["category"],
        source_hint=topic_item["source_hint"] or "관련 정부 기관 + 주요 언론에서 직접 확인",
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def main():
    max_runs = int(os.environ.get("MAX_POSTS_PER_RUN", "1"))
    for run_i in range(max_runs):
        item, remaining = pop_next_topic()
        if not item:
            print("⚠️ Topic queue is empty. Nothing to generate.", file=sys.stderr)
            sys.exit(1 if run_i == 0 else 0)

        print(f"🤖 [{run_i+1}/{max_runs}] Generating: {item['topic'][:60]}")
        md = generate(item)
        title, body = extract_title_and_body(md)
        labels, desc = extract_meta(md)
        slug = slugify(title)

        # Avoid overwriting an existing file
        if (BLOG / f"{slug}.md").exists():
            slug = f"{slug}-{datetime.now(timezone.utc).strftime('%H%M')}"

        out = write_post(title, body, labels, desc, item["category"], slug)
        print(f"✅ Wrote {out.relative_to(REPO)} ({len(body)} chars, {len(labels)} tags)")

        # Persist updated queue (topic removed) only after successful write
        QUEUE.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")
        print(f"   Queue size now: {sum(1 for ln in remaining if parse_queue_line(ln))}")


if __name__ == "__main__":
    main()
