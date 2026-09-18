# openlxl — English Vocabulary Story Learning Agent

[English](README.md) · [简体中文](README.zh-CN.md)

An English vocabulary learning mode based on FSRS spaced repetition: pick target words from your learning vocabulary → write a **mixed Chinese–English story** (Chinese narration; English appears only as the target words and words from your known-words list) → audit → record usage → wait for your "know / don't know" feedback → update memory state. New words are only written into the vocabulary after you explicitly confirm them.

> **Memory scheduling references Anki**: the spaced-repetition scheduling in this project uses the same open-source [FSRS](https://github.com/open-spaced-repetition/fsrs4anki) algorithm that [Anki](https://apps.ankiweb.net/) uses, implemented via [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs). Selection priority, forget scores and review intervals are computed consistently with the Anki ecosystem.

> **Mixed is the ramp, pure English is the summit**: English in a story is limited to "target words being tested + words on your known-words list"; everything else is Chinese. The longer that list grows, the more English appears — no switch to flip, vocabulary size *is* the throttle. Each chapter reports its English ratio so you can watch it climb toward pure English (`--mode english` is the summit mode).

This repository is an **agent preset** for [DeepSeek Harness (DSH)](https://github.com/deepseek-ai/dsh), and can also be used standalone as a Python CLI.

> See [CHANGELOG.md](CHANGELOG.md) · License [MIT](LICENSE)

## Features

- **FSRS memory scheduling**: built-in [py-fsrs 6.3.1](https://github.com/open-spaced-repetition/py-fsrs) (the spaced-repetition algorithm used by Anki); every word keeps its own `difficulty / stability / due date`.
- **Forget-score ranking**: at pick time the current forget score (`(1 - retrievability) × 100`) is computed live — words about to be forgotten float to the top, new cards default to 30, and long-forgotten "don't know" words automatically cut back in line.
- **Mixed Chinese–English writing (default)**: narration is Chinese; English is allowed for exactly three kinds of words — target words / known words from the range vocabulary / explicitly allowed proper nouns. Even function words (the, and, is…) are rejected. Every target occurrence must be bolded (hard audit check). Length counts Chinese characters + English words (default 300–800).
- **Strict audit**: all targets present / every occurrence bolded / English restricted to the three allowed kinds / mixed-length window; a story is committed only after the audit passes. The English ratio (`english_ratio`) is reported per chapter as an observation, not gated.
- **Pure-English mode (the summit)**: `--mode english` restores the legacy all-English rules (built-in function-word allowance, 180–400 words) — switch when your known-words list is long enough.
- **Layered long-form memory**: a chapter fact ledger (`chapter-ledger.jsonl`) records per-chapter facts, character/relationship changes, thread changes and consequences; a volume/story-arc outline (`plot-outline.json`) keeps the long-term direction, with a deterministic conflict detector that flags "did come" vs "never came" contradictions.
- **Extractable, confirmable style**: a style profile (`style-profile.json`) holds dimensions / must-do / avoid / confidence; candidate styles are extracted from reference fragments + reader impressions and only persisted after you confirm (`engstory_extract_style` → `engstory_confirm_style`) — never auto-overwritten.
- **On-demand context assembly**: `engstory_build_context` merges style + plot outline + facts + current state + target words into a single bounded writing-context package.
- **Dramatic chapter structure**: each chapter is required to complete "scene entry → chapter goal → obstacle → choice → consequence → concrete hook", with hard negative constraints (no repeated weather openings, no random new characters, no empty suspense, no dream explanations).
- **Always-on writing craft**: the plugin registers a dedicated system-prompt section (`plugins/craft.md` → `engstory:craft`) through the DSH prompt registry, so the writing discipline — six pre-draft checks, three drafting rules (never repeat your own recent openings / target words get dramatic weight by forget score / structure is a skeleton, not a sentence pattern), four embedding rules (inferable context / twice in two contexts / restrained density / no glossing), and a seven-dimension self-review with de-cliché diagnosis — stays present in every session instead of depending on on-demand skill loading.
- **Guide mode (`engstory-guide` skill)**: when the user asks "how do I start / what am I missing", it first runs `engstory_doctor` for a deterministic, read-only check of the real environment, then explains in plain language what goes into each empty slot; when the user wants to tune the effect, a built-in parameter map points to the exact knob (target count / story length / style / plot direction…) and explains what each parameter does and what changes after the tweak.
- **Strict batch state machine**: `TARGETS_SELECTED → WAITING_FEEDBACK → WAITING_WORD_CONFIRMATION → IDLE` — no memory update without user feedback, no new words without user confirmation.
- **Morphological lemmatization**: `sought → seek`, `stood → stand`; polysemous words are tracked as independent entries (`blue|蓝色`, `blue|忧伤`).
- **Fingerprint dedup**: re-marking the same text is skipped automatically to prevent inflated usage counts.
- **Dual usage**: DSH agent preset (conversational full loop) + standalone Python CLI (pure stdlib, Python ≥ 3.10).

## Directory Structure

```
openlxl/
├── agent.cordis.yml              # DSH agent preset composition (persona + tools + skills)
├── preset.yml                    # preset metadata
├── CHANGELOG.md                  # version changelog
├── LICENSE                       # MIT license
├── plugins/
│   ├── engstory-tools.mjs        # 10 deterministic tools (registered to the DSH agent)
│   └── craft.md                  # always-on writing-craft system-prompt section
├── skills/
│   ├── engstory-guide/
│   │   └── SKILL.md              # guide mode: setup & tuning guidance (loaded on demand)
│   └── engstory-domain/
│       ├── SKILL.md              # domain rules + fixed reply templates
│       ├── 检索/SKILL.md         # sub-skill: pick targets (CLI reference)
│       ├── 写故事/SKILL.md       # sub-skill: story loop (CLI reference)
│       ├── 更定频率/SKILL.md     # sub-skill: mark usage (CLI reference)
│       ├── 反馈/SKILL.md         # sub-skill: feedback (CLI reference)
│       ├── 写入词汇/SKILL.md     # sub-skill: write new words (CLI reference)
│       └── scripts/              # 15 Python scripts (pure stdlib)
│           ├── vocab_core.py     #   vocab IO / lemmatization / FSRS forget score
│           ├── pick.py           #   pick targets (due-driven four queues)
│           ├── mark.py           #   mark usage statistics
│           ├── feedback.py       #   apply feedback (updates FSRS)
│           ├── add.py            #   write new words
│           ├── doctor.py         #   environment check (read-only, facts layer of guide mode)
│           ├── vocab_distill.py  #   build the allowed vocabulary package
│           ├── story_audit.py    #   story audit
│           ├── range_lib.py      #   range vocabulary / function-word whitelist
│           ├── state.py          #   batch state machine
│           ├── storyline.py      #   continuous storyline state (premise / threads / chapter / consequence)
│           ├── ledger.py         #   per-chapter fact ledger (with conflict detection)
│           ├── outline.py        #   volume / story-arc outline
│           ├── style.py          #   style profile (load / extract / confirm / context)
│           └── context.py        #   assemble the bounded writing-context package
├── vendor/                       # vendored dependencies (MIT)
│   ├── fsrs/                     #   py-fsrs 6.3.1 (with its LICENSE)
│   └── typing_extensions.py      #   4.16.0
└── examples/
    ├── vocab.sample.json         # sample learning vocabulary
    └── range.sample.json         # sample range vocabulary
```

## Quick Start

### As a DSH agent preset

Prerequisites: [DeepSeek Harness (DSH)](https://github.com/deepseek-ai/dsh) and Python ≥ 3.10.

1. Clone this repository into DSH's agent presets directory (one directory per preset; the `openlxl` directory name must be kept):

   ```powershell
   # Windows
   git clone https://github.com/fanxzl/openlxl-dsh.git
   Copy-Item -Recurse .\openlxl "$env:USERPROFILE\.dsh\.agent-presets\openlxl"
   ```

   ```bash
   # Linux / macOS
   git clone https://github.com/fanxzl/openlxl-dsh.git
   cp -r openlxl ~/.dsh/.agent-presets/openlxl
   ```

2. Start DSH and create a new session with the `openlxl` preset (the agent automatically gets the 10 tools + domain skills).

3. Prepare two vocabularies (paths are up to you; pass them to the tools or via environment variables):

   | Vocabulary | Default path (env var override) | Purpose |
   |---|---|---|
   | FSRS learning vocabulary | `/workspace/vocab.json` (`ENGSTORY_VOCAB`) | words to learn: target selection / usage stats / memory feedback |
   | Range vocabulary (known-words whitelist) | `./range_vocab.json` (`ENGSTORY_RANGE`) | English words allowed to appear in stories; the longer it grows, the more English your stories carry |

4. Tell the agent "写故事" (write a story) and it runs the full loop: pick → write → audit → mark → wait for your "know/don't know" → update memory.

### As a Python CLI

Requirements: Python ≥ 3.10 (no third-party runtime dependencies; FSRS is vendored).

```bash
cd skills/engstory-domain
V="<your learning vocab path>"; R="<your range vocab path>"

# 1. Write new words (only after user confirmation)
python scripts/add.py --words "abandon 放弃, harbor 港口" --vocab "$V"

# 2. Pick 7 target words
python scripts/pick.py --vocab "$V"

# 3. Build the allowed vocabulary package (before writing a story)
python scripts/vocab_distill.py --targets "abandon,harbor" --range "$R" --vocab "$V"

# 4. Audit a story (mixed mode by default; add --mode english for the legacy rules)
python scripts/story_audit.py --text "<story text>" --targets "abandon,harbor" --range "$R"

# 5. Mark usage
python scripts/mark.py --text "<story text>" --words "abandon,harbor" --vocab "$V"

# 6. Apply feedback (after the user reports know/don't know)
python scripts/feedback.py --words "abandon 会, harbor 不会" --vocab "$V"
```

All scripts support `--json` output for programmatic use.

## Workflow & State Machine

```
Story loop (strict order):
  ① select_targets      pick 7 target words from the learning vocabulary   → TARGETS_SELECTED
  ② build_context       assemble style + plot + facts + current state + targets
  ③ prepare_story_vocab build the allowed English word package
  ④ write a 300–800 mixed-length chapter (Chinese narration; English only for targets / known words / proper nouns, targets bolded, dramatic structure)
  ⑤ audit_story         commit only if the audit passes; rewrite at most twice
  ⑥ commit_story        save story + mark usage + advance storyline/ledger → WAITING_FEEDBACK
  ⑦ apply_feedback      update FSRS only after the user reports            → WAITING_WORD_CONFIRMATION / IDLE
  ⑧ write_learning_words add out-of-range discovered words only after the user confirms
```

| Tool | Script | Action | When |
|---|---|---|---|
| `engstory_select_targets` | pick.py | pick targets, open a batch | start of each round |
| `engstory_build_context` | context.py | assemble the bounded writing-context package | before writing |
| `engstory_prepare_story_vocab` | vocab_distill.py | build the allowed vocabulary package | before writing |
| `engstory_audit_story` | story_audit.py | read-only audit | after writing |
| `engstory_commit_story` | story_audit.py + mark.py | save only if audit passes + mark usage + advance storyline/ledger | after audit passes |
| `engstory_apply_feedback` | feedback.py | update FSRS memory state | after user reports |
| `engstory_write_learning_words` | add.py | write new words | after explicit confirmation |
| `engstory_extract_style` | style.py | extract a candidate style (no write) | on reference fragments |
| `engstory_confirm_style` | style.py | persist a confirmed style profile | after user confirms |
| `engstory_doctor` | doctor.py | read-only environment check → setup checklist | on setup/config questions |

## Data Files

### Learning vocabulary (JSON)

```json
{
  "meta": { "marked": { "<text fingerprint sha1>": "2026-08-15T20:00:00+08:00" } },
  "words": {
    "harbor": {
      "gloss": "港口",
      "picks": 3, "last_pick": "2026-07-10T09:00:00+08:00",
      "uses": 1, "texts": 1, "last_use": "2026-07-15T20:00:00+08:00",
      "forms": [], "不会频次": 2,
      "card_id": 10001,
      "state": 3, "step": 0,
      "stability": 0.8, "difficulty": 6.3,
      "due": "2026-07-20T09:00:00+00:00",
      "last_review": "2026-07-15T09:00:00+00:00",
      "forget_score": 62.5
    }
  }
}
```

Field reference:

| Field | Meaning | Updated by |
|---|---|---|
| `picks` / `last_pick` | times picked / last pick time | pick.py |
| `uses` / `texts` / `last_use` | usage count / number of texts / last use | mark.py |
| `不会频次` | repeated-import count | add.py |
| `state`/`step`/`stability`/`difficulty`/`due`/`last_review`/`card_id` | FSRS card parameters | feedback.py (computed by py-fsrs) |
| `forget_score` | cached forget score (refreshed at pick/feedback time) | pick.py / feedback.py |
| `meta.marked` | fingerprints of already-marked texts (English words + Chinese characters), prevents double counting | mark.py |

Polysemous words are split into independent entries by `word|gloss` (e.g. `blue|蓝色`, `blue|忧伤`), each with its own counters and memory state.

### Range vocabulary (JSON — the known-words whitelist)

```json
{
  "words": {
    "castle":   { "gloss": "城堡" },
    "walk":     { "gloss": "走", "forms": ["walked", "walking"] }
  }
}
```

In mixed mode this is **the set of English words allowed to appear in stories** (besides targets): listed words may be embedded into the Chinese narration, and the longer the list, the denser the English. In pure-English mode (`--mode english`) it reverts to its legacy role — restricting ordinary words.

### Batch state file

Defaults to `state.json` beside the learning vocabulary (`ENGSTORY_STATE` overridable); stories default to `stories/` beside the vocabulary.

### Long-form memory files (all optional, all beside the vocabulary)

| File | Purpose | Env override |
|---|---|---|
| `storyline.json` | continuous state: premise / current chapter / open threads / chapter goal / last consequence / recap / last ending | `ENGSTORY_STORYLINE` |
| `style-profile.json` | style profile (dimensions / must-do / avoid / confidence) | `ENGSTORY_STYLE` |
| `plot-outline.json` | volume / story-arc outline (core thread / end state / arcs / permanent facts) | `ENGSTORY_OUTLINE` |
| `chapter-ledger.jsonl` | per-chapter fact ledger (facts / character changes / threads / consequences) | `ENGSTORY_LEDGER` |

## FSRS Notes

- Memory state is computed by [py-fsrs 6.3.1](https://github.com/open-spaced-repetition/py-fsrs) (MIT), the same algorithm family as Anki's FSRS.
- Forget score = `(1 - retrievability) × 100`, 0–100+, **higher means closer to forgetting and more due for practice**:
  - unreviewed new cards default to 30;
  - cards reviewed as "know" score 0–10 and gradually rise as their interval lapses;
  - cards reviewed as "don't know" climb past 30 and automatically cut back in line.
- Marking usage (`uses/texts`) only affects tie-breaking in ranking; it does **not** enter the FSRS formula directly — scheduling is driven only by feedback and elapsed time.
- The dependency directory can be pointed at an externally installed fsrs package via `ENGSTORY_FSRS` (e.g. after `pip install fsrs`, point it at its site-packages directory); the default is the bundled `vendor/`.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `ENGSTORY_VOCAB` | `/workspace/vocab.json` | FSRS learning vocabulary path |
| `ENGSTORY_RANGE` | `./range_vocab.json` | known-words whitelist path (English allowed in stories) |
| `ENGSTORY_STATE` | `state.json` beside the vocabulary | batch state file |
| `ENGSTORY_FSRS` | bundled `vendor/` | fsrs dependency directory |
| `ENGSTORY_STORYLINE` | `storyline.json` beside the vocabulary | continuous storyline state |
| `ENGSTORY_STYLE` | `style-profile.json` beside the vocabulary | style profile |
| `ENGSTORY_OUTLINE` | `plot-outline.json` beside the vocabulary | volume / story-arc outline |
| `ENGSTORY_LEDGER` | `chapter-ledger.jsonl` beside the vocabulary | chapter fact ledger |

## License

- This repository: MIT (see [LICENSE](LICENSE)).
- Vendored dependencies: [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) (MIT, see `vendor/fsrs/LICENSE`), [typing-extensions](https://github.com/python/typing_extensions) (PSF-2.0 / Apache-2.0).
- Credits: memory scheduling references [Anki](https://apps.ankiweb.net/)'s open-source [FSRS spaced-repetition algorithm](https://github.com/open-spaced-repetition/fsrs4anki); the writing-craft discipline (review dimensions, de-cliché diagnosis, pre-draft checks) was inspired by [InkOS](https://github.com/Narcooo/inkos) — ideas only, all wording and code in this repository are original and remain MIT.
