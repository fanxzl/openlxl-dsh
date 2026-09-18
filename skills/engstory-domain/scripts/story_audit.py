#!/usr/bin/env python3
"""story_audit.py — 故事严格审计（纯只读）

两种模式：
  - mixed（默认，中英混合）：中文是正文语言；英文只允许三类——目标词 / 范围词库（已会词）/
    明确专名，**功能词不豁免**（the/and/is 出现即判超纲）；目标词每次出现必须加粗；
    长度 = 汉字数 + 英文词数，默认窗口 300–800。英文占比只作观测值输出（english_ratio），
    不设闸门——占比靠范围词库生长自然爬升（混合是坡道，纯英文是坡顶）。
  - english（纯英文，坡顶/兼容）：旧规则全保留——纯英文、普通词落在允许集合（含内置功能词）、
    180–400 词窗口。

共有检查：
  - 目标词是否全部出现（多义词按独立词条计数，同一 base 出现次数 >= 拆分数才算全中）
  - 词形归并（walked → walk）后再判定，避免正常变形被误判超纲

用法：
  python story_audit.py --file story.md --targets "coffin,abrupt" --range <range.json>
  python story_audit.py --text "..." --targets "castle,blue|蓝色" --range <range.json> --json
  python story_audit.py --text "..." --targets "castle" --range <range.json> --mode english
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from range_lib import DEFAULT_RANGE, allowed_sets, is_allowed_token, load_range  # noqa: E402
from vocab_core import backward_candidates, split_key, tokenize  # noqa: E402

CJK_RE = re.compile(r"[一-鿿]")


def audit_text(text: str, target_keys: list, range_path: Path, proper_names=(),
               mode="mixed", min_length=300, max_length=800,
               min_words=180, max_words=400) -> dict:
    raw, toks = tokenize(text)
    english_words = len(toks)
    cjk_chars = len(CJK_RE.findall(text))
    length = cjk_chars + english_words

    # 目标词命中：按 base 分组，同一 base 出现次数 >= 该 base 的独立词条数才算全中
    groups = {}
    for key in target_keys:
        base, _ = split_key(key)
        groups.setdefault(base, []).append(key)

    target_hits, target_missing = {}, []
    for base, keys in groups.items():
        real = _base_occurrences(raw, toks, base)
        for idx, key in enumerate(keys):
            if idx < real:
                target_hits[key] = 1
            else:
                target_missing.append(key)

    range_words = load_range(range_path)
    # mixed：功能词不豁免——英文只允许 目标词/范围词库/专名 三类
    sets = allowed_sets(range_words, target_keys, proper_names,
                        include_function_words=(mode == "english"))
    target_bases = {split_key(k)[0] for k in target_keys}

    out_of_range, seen = [], set()
    for tok in toks:
        if tok in target_bases:
            continue
        if is_allowed_token(tok, sets["lemmas"], sets["forms"],
                            single_letters=(mode == "english")):
            continue
        if tok not in seen:
            seen.add(tok)
            out_of_range.append(tok)

    reasons = []
    unbolded = []
    if target_missing:
        reasons.append(f"目标词未全部出现：{'、'.join(target_missing)}")
    if out_of_range:
        note = ("（混合模式只允许目标词/已会词/专名用英文）" if mode == "mixed" else "")
        reasons.append(f"普通词超出允许范围{note}：{'、'.join(out_of_range[:20])}"
                       + (" 等" if len(out_of_range) > 20 else ""))

    if mode == "english":
        if not (min_words <= english_words <= max_words):
            reasons.append(f"字数 {english_words} 不在 {min_words}–{max_words} 范围内")
        if CJK_RE.search(text):
            reasons.append("故事包含中文/非英文字符")
    else:
        if not (min_length <= length <= max_length):
            reasons.append(f"混合字数 {length}（汉字 {cjk_chars} + 英文词 {english_words}）"
                           f"不在 {min_length}–{max_length} 范围内")
        unbolded = _unbolded_targets(text, target_keys)
        if unbolded:
            reasons.append(f"目标词未加粗：{'、'.join(unbolded)}")

    english_ratio = round(english_words / length, 3) if length else 0.0
    return {
        "pass": not reasons,
        "mode": mode,
        "length": length,
        "cjk_chars": cjk_chars,
        "english_words": english_words,
        "english_ratio": english_ratio,
        "word_count": english_words,      # 兼容旧字段：= 英文词数
        "target_hits": target_hits,
        "target_missing": target_missing,
        "out_of_range": out_of_range,
        "unbolded_targets": unbolded,
        "reasons": reasons,
    }


def _base_occurrences(low: str, toks: list, base: str) -> int:
    """返回某个 base（词元）在文本中的出现次数，含词形归并。"""
    n = 0
    for tok in toks:
        if tok == base:
            n += 1
            continue
        if base in backward_candidates(tok):
            n += 1
    return n


def _unbolded_targets(text: str, target_keys: list) -> list:
    """mixed 模式硬检查：目标词每次出现都必须被 **…** 包裹。

    加粗是「待检测词 vs 已会词」的唯一视觉锚点。做法：把所有 **…** 区块内的文本
    单独 token 化，对比目标词总出现次数与加粗出现次数。短语型 key（含空格）跳过——
    token 计数本就不覆盖它们。
    """
    raw, toks = tokenize(text)
    bold_blocks = re.findall(r"\*\*(.+?)\*\*", text, re.S)
    _, bold_toks = tokenize(" ".join(bold_blocks)) if bold_blocks else ("", [])
    out = []
    for base in {split_key(k)[0] for k in target_keys}:
        if " " in base:
            continue
        total = _base_occurrences(raw, toks, base)
        if total == 0:
            continue    # 完全没出现，交给 target_missing 报
        bolded = _base_occurrences(raw, bold_toks, base)
        if bolded < total:
            out.append(f"{base}（{total - bolded} 处未加粗）")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="审计：检查故事目标词、允许英文范围与长度")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="直接传入故事文本")
    src.add_argument("--file", help="故事文件路径")
    ap.add_argument("--targets", required=True, help="逗号分隔的目标词条 key")
    ap.add_argument("--range", default=str(DEFAULT_RANGE), help="范围词汇库 json 路径")
    ap.add_argument("--proper-names", help="逗号分隔的允许专有名词")
    ap.add_argument("--mode", choices=["mixed", "english"], default="mixed",
                    help="mixed=中英混合（默认）；english=纯英文（旧规则）")
    ap.add_argument("--min-length", type=int, default=300,
                    help="mixed 模式混合字数下限（汉字 + 英文词），默认 300")
    ap.add_argument("--max-length", type=int, default=800,
                    help="mixed 模式混合字数上限，默认 800")
    ap.add_argument("--min-words", type=int, default=180, help="english 模式词数下限，默认 180")
    ap.add_argument("--max-words", type=int, default=400, help="english 模式词数上限，默认 400")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    if args.text:
        text = args.text
    else:
        p = Path(args.file)
        if not p.exists():
            sys.exit(f"ERROR: 文件不存在：{p}")
        text = p.read_text(encoding="utf-8-sig", errors="replace")

    target_keys = [t.strip().lower() for t in args.targets.split(",") if t.strip()]
    proper_names = [p.strip() for p in (args.proper_names or "").split(",") if p.strip()]

    result = audit_text(text, target_keys, Path(args.range), proper_names,
                        mode=args.mode, min_length=args.min_length, max_length=args.max_length,
                        min_words=args.min_words, max_words=args.max_words)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0

    if result["pass"]:
        if result["mode"] == "english":
            print(f"审计通过：{result['word_count']} 词，目标词全中"
                  + (f"（{len(result['target_hits'])} 个）" if result["target_hits"] else ""))
        else:
            print(f"审计通过：混合字数 {result['length']}"
                  f"（汉字 {result['cjk_chars']} + 英文词 {result['english_words']}），"
                  f"英文占比 {result['english_ratio']:.0%}，目标词全中"
                  + (f"（{len(result['target_hits'])} 个）" if result["target_hits"] else ""))
    else:
        print(f"审计失败：{'；'.join(result['reasons'])}")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
