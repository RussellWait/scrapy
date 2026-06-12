from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CODE_ANALYSIS_DIR = ROOT / "_code_analysis"
CREATE_MD_INFO = CODE_ANALYSIS_DIR / "CREATE_MD_INFO.txt"
TIMESTAMP_RE = re.compile(
    r"\s+—\s+(?:\d{4}-\d{2}-\d{2} \d{2}:\d{2}|【\d{4}-\d{2}-\d{2} \d{2}:\d{2}】)$"
)


def beijing_now() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M")


def format_timestamp(timestamp: str) -> str:
    return f"【{timestamp}】"


def parse_tree_line(line: str) -> tuple[int, str, bool] | None:
    depth = 0
    rest = line
    while rest.startswith("│   ") or rest.startswith("    "):
        depth += 1
        rest = rest[4:]
    if rest.startswith("├── ") or rest.startswith("└── "):
        name = rest[4:]
        is_dir = name.endswith("/")
        clean_name = name.rstrip("/")
        if not is_dir:
            clean_name = TIMESTAMP_RE.sub("", clean_name)
        return depth, clean_name, is_dir
    return None


def md_to_src_parts(md_path: Path) -> tuple[str, ...]:
    md_path = md_path.resolve()
    md_rel = md_path.relative_to(CODE_ANALYSIS_DIR)
    if md_rel.suffix != ".md":
        raise ValueError(f"not an md file: {md_path}")
    return md_rel.with_suffix(".py").parts


def iter_tree_entries(
    lines: list[str],
) -> list[tuple[int, int, str, bool, tuple[str, ...]]]:
    stack: list[str] = []
    entries: list[tuple[int, int, str, bool, tuple[str, ...]]] = []

    for idx, line in enumerate(lines):
        parsed = parse_tree_line(line)
        if parsed is None:
            continue

        depth, name, is_dir = parsed
        current_parts = ("scrapy",) + tuple(stack[:depth]) + (name,)

        if is_dir:
            if len(stack) <= depth:
                stack.append(name)
            else:
                stack[depth] = name
                del stack[depth + 1 :]
        entries.append((idx, depth, name, is_dir, current_parts))

    return entries


def suggest_insertion(target_parts: tuple[str, ...], lines: list[str]) -> str:
    entries = iter_tree_entries(lines)
    parent_parts = target_parts[:-1]
    file_name = target_parts[-1]

    parent_entry: tuple[int, int, str, bool, tuple[str, ...]] | None = None
    for entry in entries:
        _, _, _, is_dir, current_parts = entry
        if is_dir and current_parts == parent_parts:
            parent_entry = entry
            break

    if parent_entry is not None:
        parent_idx, parent_depth, _, _, _ = parent_entry
        insert_after_line = parent_idx + 1
        for idx, depth, _, _, _ in entries:
            if idx <= parent_idx:
                continue
            if depth <= parent_depth:
                break
            insert_after_line = idx + 1

        return (
            f"SUGGEST parent={'/'.join(parent_parts)}/ ; "
            f"insert after CREATE_MD_INFO.txt line {insert_after_line} ; "
            f"entry {file_name} — 【<北京时间>】"
        )

    existing_dir_parts = ("scrapy",)
    for entry in entries:
        _, _, _, is_dir, current_parts = entry
        if not is_dir:
            continue
        if (
            len(current_parts) > len(existing_dir_parts)
            and target_parts[: len(current_parts)] == current_parts
        ):
            existing_dir_parts = current_parts

    missing_parts = parent_parts[len(existing_dir_parts) :]
    return (
        f"SUGGEST missing parent directory {'/'.join(parent_parts)}/ ; "
        f"deepest existing directory is {'/'.join(existing_dir_parts)}/ ; "
        f"missing path {'/'.join(missing_parts) or '(none)'} ; "
        f"entry {file_name} — 【<北京时间>】"
    )


def update_entry(action: str, md_path: Path, timestamp: str) -> tuple[bool, str | None]:
    target_parts = md_to_src_parts(md_path)
    lines = CREATE_MD_INFO.read_text(encoding="utf-8").splitlines()
    entries = iter_tree_entries(lines)

    for idx, _, _, is_dir, current_parts in entries:
        if is_dir or current_parts != target_parts:
            continue

        base = TIMESTAMP_RE.sub("", lines[idx])
        if action == "done":
            lines[idx] = f"{base} — {format_timestamp(timestamp)}"
        elif action == "pending":
            lines[idx] = base
        else:
            raise ValueError(f"unknown action: {action}")
        CREATE_MD_INFO.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, None

    return False, suggest_insertion(target_parts, lines)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: update_create_md_info.py <done|pending> <md-file> [<md-file> ...]")
        return 1

    action = sys.argv[1]
    timestamp = beijing_now()
    exit_code = 0

    for raw_path in sys.argv[2:]:
        md_path = Path(raw_path)
        try:
            changed, suggestion = update_entry(action, md_path, timestamp)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {md_path}: {exc}")
            exit_code = 1
            continue

        if not changed:
            print(f"MISS  {md_path}")
            if suggestion:
                print(suggestion)
            exit_code = 1
            continue

        if action == "done":
            print(f"DONE  {md_path} -> {timestamp}")
        else:
            print(f"RESET {md_path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
