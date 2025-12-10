#!/usr/bin/env python3
"""
anthropic_table_scraper.py

Crawl and extract prompt blocks from Anthropic-style docs pages that store prompts
in tables with left-column labels like "System", "User", "Example output".

Outputs a JSON file with one object per prompt block:
{
  "id": "<auto id>",
  "system": "...",            # optional
  "user": "...",              # optional
  "examples": ["...", ...],   # list of example outputs / assistant outputs
  "source_url": "...",
  "page_title": "...",
  "raw_blocks": [ { "label": "...", "text": "..." }, ... ]
}

Usage:
  python anthropic_table_scraper.py --start-url "https://platform.claude.com/docs/en/resources/prompt-library/website-wizard" \
      --max-pages 200 --rate 1.5 --out anthropic_prompts_clean.json

Notes:
 - The script checks robots.txt and will abort if the site disallows crawling the docs root.
 - Be respectful with --rate (seconds between requests).
 - Inspect and tune the LABEL_WHITELIST if the site uses slightly different label text.
"""

import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import json
import re
import sys
import hashlib
from typing import List, Dict, Any

# set your email/contact
USER_AGENT = "AnthropicPromptScraper/1.0 (+youremail@example.com)"
REQUEST_TIMEOUT = 20.0

# Labels we care about (normalized lowercase)
LABEL_WHITELIST = {
    "system", "user", "assistant", "example output", "example", "output", "example-output"
}

# Heuristic trigger words for fallback detection
PROMPT_TRIGGER_RE = re.compile(
    r"\b(Your task is|Write|Create|Build|Design|Train|Summarize|Explain|Generate|Convert|Compose)\b", re.I)

# -------------------------
# Helpers
# -------------------------


def safe_get(url: str, headers: Dict[str, str], timeout: float):
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[WARN] fetch failed for {url}: {e}")
        return None


def check_robots(start_url: str, headers: Dict[str, str]) -> bool:
    parsed = urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        r = requests.get(robots_url, headers=headers, timeout=REQUEST_TIMEOUT)
        # if no robots.txt, we proceed but warn
        if r.status_code != 200:
            print(
                f"[INFO] robots.txt not found (status {r.status_code}) at {robots_url}. Proceed with caution.")
            return True
        txt = r.text
        # Naive check: disallow root or disallow /docs path
        if re.search(r"Disallow:\s*/\s*$", txt, re.I | re.M):
            print(
                "[ERROR] robots.txt explicitly disallows indexing the site root. Aborting.")
            return False
        # If site disallows /docs or similar, warn
        if re.search(r"Disallow:\s*/docs", txt, re.I | re.M):
            print(
                "[WARN] robots.txt disallows /docs — you should not crawl docs pages. Aborting.")
            return False
        return True
    except Exception as e:
        print("[WARN] Failed to fetch robots.txt:", e)
        return False


def normalize_label(text: str) -> str:
    t = re.sub(r"\s+", " ", text.strip()).lower()
    return t


def extract_table_prompts(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Find table rows and map left cell -> right cell for known labels.
    Returns list of small dicts: [{ "label": label, "text": text }, ...]
    """
    out = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            tds = tr.find_all(["td", "th"])
            if len(tds) < 2:
                continue
            left = tds[0].get_text(separator=" ").strip()
            right = tds[1].get_text(separator="\n").strip()
            if not left or not right:
                continue
            left_norm = normalize_label(left)
            if left_norm in LABEL_WHITELIST:
                out.append({"label": left_norm, "text": right})
    return out


def extract_heading_examples(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Find headings like 'Example output' followed by a block (pre/div) and return them
    as label/text pairs. Helps capture pages using headings instead of tables.
    """
    out = []
    for h in soup.find_all(re.compile("^h[1-6]$")):
        txt = h.get_text().strip().lower()
        if "example" in txt:
            # find next sibling blocks up to a few steps
            el = h.find_next_sibling()
            attempts = 0
            while el and attempts < 6:
                text = el.get_text(separator="\n").strip()
                if text:
                    out.append({"label": "example output", "text": text})
                    break
                el = el.find_next_sibling()
                attempts += 1
    return out


def fallback_td_detection(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Fallback: find any <td> that looks like a prompt (imperative verbs)
    """
    out = []
    for td in soup.find_all("td"):
        txt = td.get_text(separator=" ").strip()
        if len(txt) < 20:
            continue
        if PROMPT_TRIGGER_RE.search(txt):
            out.append({"label": "candidate", "text": txt})
    return out


def aggregate_label_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Rows: sequence of {label, text} from a page.
    We aggregate consecutively into prompt objects:
      - A 'system' row starts a new object
      - 'user' attaches to current object
      - 'example' appended into examples list
    """
    aggregated = []
    cur = None
    for r in rows:
        lbl = r.get("label")
        txt = r.get("text")
        if lbl == "system":
            if cur:
                aggregated.append(cur)
            cur = {"system": txt, "user": None, "examples": [],
                   "raw_blocks": [{"label": "system", "text": txt}]}
        elif lbl == "user":
            if cur is None:
                cur = {"system": None, "user": txt, "examples": [],
                       "raw_blocks": [{"label": "user", "text": txt}]}
            else:
                cur["user"] = txt
                cur["raw_blocks"].append({"label": "user", "text": txt})
        elif lbl and "example" in lbl:
            if cur is None:
                cur = {"system": None, "user": None, "examples": [
                    txt], "raw_blocks": [{"label": "example", "text": txt}]}
            else:
                cur.setdefault("examples", []).append(txt)
                cur["raw_blocks"].append({"label": "example", "text": txt})
        else:
            # non-recognized label: just append as raw block if we have a cur
            if cur is None:
                cur = {"system": None, "user": None, "examples": [],
                       "raw_blocks": [{"label": lbl or "unknown", "text": txt}]}
            else:
                cur["raw_blocks"].append(
                    {"label": lbl or "unknown", "text": txt})
    if cur:
        aggregated.append(cur)
    # filter out empty objects (no system/user/examples)
    filtered = []
    for obj in aggregated:
        if (obj.get("system") and obj.get("user")) or (obj.get("system") and obj.get("examples")) or (obj.get("user") and obj.get("examples")):
            filtered.append(obj)
        else:
            # accept single system-only objects too (some pages present only system)
            if obj.get("system"):
                filtered.append(obj)
    return filtered


def page_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return ""

# -------------------------
# Main crawler
# -------------------------


def crawl(start_url: str, max_pages: int = 200, rate: float = 1.0, out_file: str = "anthropic_prompts.json"):
    headers = {"User-Agent": USER_AGENT}
    if not check_robots(start_url, headers):
        print("[ABORT] robots.txt prevented crawling.")
        return []

    parsed_root = urlparse(start_url)
    root_netloc = parsed_root.netloc
    queue = deque([start_url])
    visited = set()
    collected = []
    pages = 0

    while queue and pages < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        print(f"[VISIT] {url}")
        html = safe_get(url, headers, REQUEST_TIMEOUT)
        time.sleep(rate)
        if not html:
            visited.add(url)
            continue
        soup = BeautifulSoup(html, "html.parser")

        # First, attempt table-based extraction
        rows = extract_table_prompts(soup)
        # If none, try heading-based
        if not rows:
            rows = extract_heading_examples(soup)
        # If still none, fallback to td detection
        if not rows:
            rows = fallback_td_detection(soup)

        prompt_objs = aggregate_label_rows(rows)
        # attach provenance
        for p in prompt_objs:
            entry = {
                "id": hashlib.sha1((url + (p.get("system") or "") + (p.get("user") or "")).encode("utf-8")).hexdigest(),
                "system": p.get("system"),
                "user": p.get("user"),
                "examples": p.get("examples", []),
                "raw_blocks": p.get("raw_blocks", []),
                "source_url": url,
                "page_title": page_title(soup)
            }
            collected.append(entry)
            print(
                f"  [FOUND] system={'Y' if entry['system'] else 'N'} user={'Y' if entry['user'] else 'N'} examples={len(entry['examples'])}")

        # enqueue internal links on same domain
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("mailto:") or href.startswith("javascript:") or href.startswith("tel:"):
                continue
            full = urljoin(url, href).split('#')[0]
            p = urlparse(full)
            if p.scheme in ("http", "https") and p.netloc == root_netloc:
                # skip asset-like and file-like paths
                if full.endswith((".png", ".jpg", ".css", ".js", ".svg")):
                    continue
                if full not in visited and full not in queue:
                    queue.append(full)

        visited.add(url)
        pages += 1

    # dedupe collected by id
    by_id = {}
    for e in collected:
        if e["id"] not in by_id:
            by_id[e["id"]] = e
        else:
            # merge examples/metadata
            existing = by_id[e["id"]]
            existing["examples"] = list(
                set(existing.get("examples", []) + e.get("examples", [])))
            existing["raw_blocks"].extend(e.get("raw_blocks", []))
    results = list(by_id.values())
    print(f"[DONE] Collected {len(results)} prompt objects from crawl.")
    # Save
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[SAVED] {out_file}")
    return results

# -------------------------
# CLI
# -------------------------


def main_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-url", required=True,
                        help="Starting Anthropic prompt docs URL (example: website-wizard page)")
    parser.add_argument("--max-pages", type=int,
                        default=200, help="Max pages to crawl")
    parser.add_argument("--rate", type=float, default=1.0,
                        help="Seconds between requests (rate limit)")
    parser.add_argument(
        "--out", default="anthropic_prompts_extracted.json", help="Output JSON file path")
    args = parser.parse_args()

    try:
        crawl(args.start_url, max_pages=args.max_pages,
              rate=args.rate, out_file=args.out)
    except KeyboardInterrupt:
        print("[INTERRUPT] Stopping crawl early.")
        sys.exit(0)


if __name__ == "__main__":
    main_cli()
