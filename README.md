# Taxonomy of Visual

A system for collecting visual references, tagging *how* they communicate (not just how they look), and turning that into on-brand generations for VG Saveur (butter), gelato and Pat's personal brand.

Three layers per image:
1. **Idea**: the technique that carries the message (pattern break, form substitution, gaze cue…).
2. **Ingredients**: the 2–3 standout look decisions (lighting, palette, texture, medium, type, casting).
3. **Register**: whose taste it serves (mainstream, cultural, counter, elite, commercial).

"Good" is per brand: it comes from Pat's approve/reject, not from a model's opinion.

## What's here

| Path | What |
|---|---|
| `research/jason-murray-analysis.md` | Analysis of Jason Murray's channel, frameworks and his Iris™ taxonomy |
| `research/channel-stats.md` | Performance of his posts by format (generated) |
| `taxonomy/seed-taxonomy.yaml` | Draft taxonomy v0.1: techniques with prompt patterns, ingredients, registers, diagnostics, quality rubric |
| `tools/tiktok_corpus.py` | Fetches caption, stats and auto-transcript for public TikTok videos (stdlib) |
| `tools/channel_stats.py` | Turns a corpus into the stats page |
| `data/raw/` | Local only (git-ignored): third-party captions, transcripts and images |

## Run

```bash
python3 tools/tiktok_corpus.py --user jason_swet --ids-file data/raw/jason_swet/ids.txt --out data/raw/jason_swet/posts.jsonl
python3 tools/channel_stats.py data/raw/jason_swet/posts.jsonl > research/channel-stats.md
```

## Planned

1. Reference intake: save an image with its source link and credit (Are.na, Cosmos, film-still sites, brand campaigns).
2. Local tagging with Liquid LFM3-VL-2B via llama.cpp (b11960+): yes/no per technique, with evidence, plus the ingredient fields.
3. A review queue where Pat approves or rejects tags and references per brand, which builds each brand's taste profile.
4. A gold set of about 100 hand-labelled images to measure the tagger before trusting it.
5. Generation: technique + brand style card → prompt; the removal test and diagnostics to revise outputs.

Note: this repository is public. Keep third-party images, transcripts and anything private out of git.
