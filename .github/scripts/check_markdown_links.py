"""Fail when a tracked Markdown file links to a repository path that does not exist.

Only relative links are checked. External URLs, mailto links and pure in-page
anchors are skipped because they cannot be verified offline.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|!\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "tel:")


def tracked_markdown(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=root, check=True, capture_output=True, text=True
    ).stdout
    return [root / line for line in out.splitlines() if line]


def broken_links(root: Path, md: Path) -> list[tuple[int, str]]:
    problems: list[tuple[int, str]] = []
    in_fence = False
    for lineno, line in enumerate(md.read_text(encoding="utf-8").splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = re.sub(r"`[^`]*`", "", line)
        for match in LINK.finditer(line):
            target = match.group(1) or match.group(2)
            if not target or target.startswith(SKIP_PREFIXES):
                continue
            path_part = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not path_part:
                continue
            base = root if path_part.startswith("/") else md.parent
            resolved = (base / path_part.lstrip("/")).resolve()
            if not resolved.exists():
                problems.append((lineno, target))
    return problems


def main() -> int:
    root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True
        ).stdout.strip()
    )
    failures = 0
    for md in tracked_markdown(root):
        for lineno, target in broken_links(root, md):
            failures += 1
            print(f"{md.relative_to(root).as_posix()}:{lineno}: broken link -> {target}")
    if failures:
        print(f"{failures} broken relative link(s)")
        return 1
    print("All relative Markdown links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
