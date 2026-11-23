#!/usr/bin/env python3
"""Fetch caption, stats and auto-transcript for public TikTok videos.

Usage:
  python3 tools/tiktok_corpus.py --user jason_swet --ids-file data/raw/jason_swet/ids.txt \
      --out data/raw/jason_swet/posts.jsonl

Reads each public video page, takes the page's own JSON (caption, stats, duration)
and, when TikTok has made one, the English auto-caption track (WebVTT).
Already-fetched ids in --out are skipped, so the run can be resumed.
Stdlib only. Polite by default: one request pair per --delay seconds.

The output is third-party content: keep it local (data/raw is git-ignored).
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
SCRIPT_RE = re.compile(
    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', re.S)


def get(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def vtt_to_text(vtt: str) -> str:
    lines = []
    for line in vtt.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT" or "-->" in line or line.isdigit():
            continue
        lines.append(line)
    return " ".join(lines)


def created_at(video_id: str) -> str:
    # TikTok ids carry the Unix time in their top 32 bits.
    return dt.datetime.fromtimestamp(int(video_id) >> 32, dt.timezone.utc).date().isoformat()


def fetch(user: str, video_id: str) -> dict:
    html = get(f"https://www.tiktok.com/@{user}/video/{video_id}")
    m = SCRIPT_RE.search(html)
    if not m:
        return {"id": video_id, "error": "no page data (blocked or removed)"}
    data = json.loads(m.group(1))
    item = (data.get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail", {})
            .get("itemInfo", {}).get("itemStruct"))
    if not item:
        return {"id": video_id, "error": "no item in page data"}
    stats = item.get("stats", {})
    subs = item.get("video", {}).get("subtitleInfos") or []
    sub = next((s for s in subs if s.get("Format") == "webvtt"
                and s.get("LanguageCodeName", "").startswith("eng")), None)
    transcript = ""
    if sub and sub.get("Url"):
        try:
            transcript = vtt_to_text(get(sub["Url"]))
        except Exception as e:  # transcript is optional
            transcript = f"[transcript fetch failed: {e}]"
    return {
        "id": video_id,
        "url": f"https://www.tiktok.com/@{user}/video/{video_id}",
        "created": created_at(video_id),
        "duration_s": item.get("video", {}).get("duration"),
        "plays": int(stats.get("playCount") or 0),
        "likes": int(stats.get("diggCount") or 0),
        "saves": int(stats.get("collectCount") or 0),
        "shares": int(stats.get("shareCount") or 0),
        "comments": int(stats.get("commentCount") or 0),
        "caption": item.get("desc", ""),
        "transcript": transcript,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--ids-file", required=True, help="one video id per line, or comma-separated")
    ap.add_argument("--out", required=True)
    ap.add_argument("--delay", type=float, default=2.0)
    a = ap.parse_args()

    ids = [x for x in re.split(r"[\s,]+", pathlib.Path(a.ids_file).read_text()) if x.isdigit()]
    out = pathlib.Path(a.out)
    done = set()
    if out.exists():
        good = []
        for line in out.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # a line cut off by an interrupted run
            if "error" not in rec and rec["id"] not in done:
                done.add(rec["id"])
                good.append(line)
        out.write_text("".join(l + "\n" for l in good))  # drop broken lines and duplicates
    todo = [i for i in ids if i not in done]
    print(f"{len(ids)} ids, {len(done)} already fetched, {len(todo)} to fetch", file=sys.stderr)

    errors = 0
    with out.open("a") as f:
        for n, vid in enumerate(todo, 1):
            try:
                rec = fetch(a.user, vid)
            except Exception as e:
                rec = {"id": vid, "error": str(e)}
            if "error" in rec:
                errors += 1
                print(f"[{n}/{len(todo)}] {vid} ERROR {rec['error']}", file=sys.stderr)
                if errors >= 5 and errors == n:
                    print("first 5 all failed: stopping (likely blocked)", file=sys.stderr)
                    return 1
            else:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[{n}/{len(todo)}] {vid} {rec['created']} plays={rec['plays']} "
                      f"saves={rec['saves']} transcript={'yes' if rec['transcript'] else 'no'}",
                      file=sys.stderr)
            time.sleep(a.delay)
    return 0


if __name__ == "__main__":
    sys.exit(main())
