#!/usr/bin/env python3
"""doctor.py — 环境体检（纯标准库，纯只读：不修改任何文件）

逐项检查 openlxl 跑起来所需的条件，输出「有什么 / 缺什么 / 缺的怎么补」。
每项都带小白能懂的说明（label）与补上方法（fix），供引导技能翻译给用户。

用法：
  python doctor.py                              # 按默认路径与环境变量检查
  python doctor.py --vocab <学习库.json> --range <范围库.json>
  python doctor.py --json                       # JSON 输出（供工具层解析）

退出码：0 = 必修项全齐；1 = 有必修项缺失或损坏。
"""

import argparse
import json
import os
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# 仓库根（…/openlxl），examples/ 样品就在那里
REPO_ROOT = Path(__file__).resolve().parents[3]

# 默认路径与 vocab_core.py / range_lib.py 保持一致
FALLBACK_VOCAB = r"/workspace/vocab.json"
FALLBACK_RANGE = "range_vocab.json"

ENV_VARS = [
    ("ENGSTORY_VOCAB", "学习词库路径"),
    ("ENGSTORY_RANGE", "范围词库路径"),
    ("ENGSTORY_STATE", "批次状态文件"),
    ("ENGSTORY_FSRS", "fsrs 依赖目录"),
    ("ENGSTORY_STORYLINE", "连载状态文件"),
    ("ENGSTORY_STYLE", "风格配置文件"),
    ("ENGSTORY_OUTLINE", "剧情总纲文件"),
    ("ENGSTORY_LEDGER", "章节事实账本"),
]


def _resolve(given: str | None, env_name: str, fallback: str) -> tuple[Path, str]:
    """三路解析路径：显式参数 > 环境变量 > 默认。返回 (路径, 来源)。"""
    if given:
        return Path(given), "explicit"
    if os.environ.get(env_name):
        return Path(os.environ[env_name]), "env"
    p = Path(fallback)
    return (p if p.is_absolute() else Path.cwd() / p), "default"


def _src_note(src: str, flag: str, env_name: str) -> str:
    if src == "env":
        return f"（来自环境变量 {env_name}）"
    if src == "default":
        return f"（默认路径，可用 {flag} 或 {env_name} 改）"
    return ""


def _find_fsrs() -> Path | None:
    """与 feedback.py 相同的候选顺序找 fsrs 依赖目录。"""
    for cand in (os.environ.get("ENGSTORY_FSRS"),
                 str(REPO_ROOT / "vendor"),
                 str(REPO_ROOT / "fsrs_pkg")):
        if cand and ((Path(cand) / "fsrs").is_dir() or (Path(cand) / "fsrs.py").exists()):
            return Path(cand)
    return None


def _check_vocab_file(path: Path) -> tuple[bool, str]:
    """检查一个词库 json：存在 → 能解析 → words 是字典。返回 (ok, detail)。"""
    if not path.exists():
        return False, f"文件不存在：{path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as e:
        return False, f"文件存在但不是合法 JSON：{path}（{e}）"
    words = data.get("words")
    if not isinstance(words, dict):
        return False, f"文件里没有 \"words\" 词表：{path}"
    return True, f"{path}（{len(words)} 个词）"


def _sample_ref(name: str, skeleton: str) -> str:
    """fix 里引用 examples/ 样品；部署副本不含 examples/ 时退化为内联最小骨架。"""
    sample = REPO_ROOT / "examples" / name
    if sample.exists():
        return f"照 {sample} 的样子建一个 JSON 文件"
    return f"新建一个 JSON 文件，最小内容：{skeleton}"


def collect(vocab_path: Path, vocab_src: str, range_path: Path, range_src: str) -> list[dict]:
    items = []

    v = sys.version_info
    items.append({
        "id": "python", "ok": v >= (3, 10), "required": True,
        "label": "Python 运行环境（跑脚本用的解释器）",
        "detail": f"当前 {v.major}.{v.minor}.{v.micro}，要求 ≥ 3.10",
        "fix": "安装 Python 3.10 或更新版本（python.org 下载，安装时勾选 Add to PATH）",
    })

    fsrs_dir = _find_fsrs()
    items.append({
        "id": "fsrs", "ok": fsrs_dir is not None, "required": True,
        "label": "记忆算法组件（FSRS，决定每个词什么时候该复习）",
        "detail": f"找到于 {fsrs_dir}" if fsrs_dir else "vendor/ 与 fsrs_pkg/ 都没找到 fsrs 包",
        "fix": "把仓库完整解压（vendor/ 目录要一起在），不要只复制 scripts/；"
               "或 pip install fsrs 后设 ENGSTORY_FSRS 指向其所在目录",
    })

    ok, detail = _check_vocab_file(vocab_path)
    items.append({
        "id": "vocab", "ok": ok, "required": True,
        "label": "学习词库（真正要学的词存在这里，选词/反馈都读写它）",
        "detail": detail + _src_note(vocab_src, "--vocab", "ENGSTORY_VOCAB"),
        "fix": _sample_ref("vocab.sample.json", '{"meta": {}, "words": {}}')
               + "（词可以留空，后面让 agent 帮你加），然后告诉 agent 它的路径",
    })

    ok, detail = _check_vocab_file(range_path)
    items.append({
        "id": "range", "ok": ok, "required": True,
        "label": "已会词白名单（故事里允许出现的英文词；词越多，故事里的英文越密）",
        "detail": detail + _src_note(range_src, "--range", "ENGSTORY_RANGE"),
        "fix": _sample_ref("range.sample.json",
                           '{"words": {"castle": {"gloss": "城堡"}, "walk": {"gloss": "走", "forms": ["walked", "walking"]}}}')
               + "，把用户已掌握的常用词填进去",
    })

    # 可选文件：默认都在学习库同目录，各有环境变量可改
    beside = vocab_path.parent
    optionals = [
        ("state", "ENGSTORY_STATE", "state.json", "批次状态（记录进行到流程的哪一步）"),
        ("storyline", "ENGSTORY_STORYLINE", "storyline.json", "连载状态（故事主线/章节/线索）"),
        ("style", "ENGSTORY_STYLE", "style-profile.json", "风格配置（故事的文风偏好）"),
        ("outline", "ENGSTORY_OUTLINE", "plot-outline.json", "剧情总纲（长篇的卷/弧方向）"),
        ("ledger", "ENGSTORY_LEDGER", "chapter-ledger.jsonl", "章节事实账本（每章发生了什么）"),
    ]
    for oid, env, fname, label in optionals:
        p = Path(os.environ.get(env, str(beside / fname)))
        items.append({
            "id": oid, "ok": p.exists(), "required": False, "label": label,
            "detail": str(p) if p.exists() else f"尚未创建（{p}）",
            "fix": "不用管：用到时自动生成；想预置风格/总纲也可以自己先建",
        })

    stories_dir = beside / "stories"
    n = len(list(stories_dir.glob("*.md"))) if stories_dir.is_dir() else 0
    items.append({
        "id": "stories", "ok": stories_dir.is_dir(), "required": False,
        "label": "故事存档目录（写好的章节都存在这）",
        "detail": f"{stories_dir}（已有 {n} 章）" if stories_dir.is_dir() else f"尚未创建（{stories_dir}）",
        "fix": "不用管：第一次提交故事时自动创建",
    })

    set_vars = [f"{k}={os.environ[k]}" for k, _ in ENV_VARS if os.environ.get(k)]
    items.append({
        "id": "env", "ok": True, "required": False,
        "label": "环境变量（告诉脚本文件都在哪的另一方式）",
        "detail": "已设置：" + "、".join(set_vars) if set_vars else "一个都没设（全部走默认路径或工具参数）",
        "fix": "不是必须；词库不在默认位置时，设 ENGSTORY_VOCAB / ENGSTORY_RANGE 最省事",
    })
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description="环境体检：检查 openlxl 跑起来的条件（只读）")
    ap.add_argument("--vocab", help="学习词库 json 路径（默认：ENGSTORY_VOCAB 或内置默认）")
    ap.add_argument("--range", help="范围词库 json 路径（默认：ENGSTORY_RANGE 或内置默认）")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    vocab_path, vocab_src = _resolve(args.vocab, "ENGSTORY_VOCAB", FALLBACK_VOCAB)
    range_path, range_src = _resolve(args.range, "ENGSTORY_RANGE", FALLBACK_RANGE)
    items = collect(vocab_path, vocab_src, range_path, range_src)
    all_ok = all(i["ok"] for i in items if i["required"])

    if args.json:
        print(json.dumps({"ok": all_ok, "items": items}, ensure_ascii=False, indent=1))
        return 0 if all_ok else 1

    for i in items:
        mark = "✓" if i["ok"] else ("✗" if i["required"] else "○")
        print(f"{mark} {i['label']}")
        print(f"  {i['detail']}")
        if not i["ok"]:
            print(f"  补上方法：{i['fix']}")
    print("体检结论：" + ("必修项全齐，可以开始写故事。" if all_ok else "有必修项缺失，按上面的「补上方法」逐项补齐。"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
