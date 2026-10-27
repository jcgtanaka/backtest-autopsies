#!/usr/bin/env python3
"""Check-only publish gate for backtest-autopsies.

Fails (exit 1) when the repository looks like it would publish raw data or
private details. It never edits files.

Checks:
  * notebooks: markdown cells, text outputs, code-cell source and metadata
    (base64 image blobs are allow-listed)
  * markdown files
  * .gitignore carries the required data patterns
  * no file above 5 MB and no data-extension files

Usage: python tools/publish_gate.py [repo_root]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024

REQUIRED_GITIGNORE = [
    "data/",
    "*.parquet",
    "*.dbn",
    ".env",
    ".ipynb_checkpoints/",
    "__pycache__/",
    "private/",
]

DATA_EXTENSIONS = (
    ".parquet", ".dbn", ".dbn.zst", ".csv", ".csv.gz", ".feather",
    ".h5", ".hdf5", ".pkl", ".pickle", ".arrow", ".sqlite", ".db",
)

SKIP_DIRS = {
    ".git", ".ipynb_checkpoints", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".mypy_cache", ".venv", "venv", "node_modules",
}

# Local account names to block in published content. Read from the environment so no
# real username is committed: PUBLISH_GATE_USERNAMES="name1,name2".
USERNAMES = tuple(u.strip() for u in os.environ.get("PUBLISH_GATE_USERNAMES", "").split(",") if u.strip())

EM_DASH = chr(0x2014)

# (rule, compiled regex, applies_to_code_source)
LINE_RULES: list[tuple[str, re.Pattern[str], bool]] = [
    ("dataframe", re.compile(r"\[\d+ rows x \d+ columns\]"), False),
    (
        "price-row",
        re.compile(
            r"(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})[T \d:.+\-Z]*[\s|,;]+"
            r"(?:-?\d+\.\d{2,}[\s|,;]+){2,}-?\d+\.\d{2,}"
        ),
        False,
    ),
    ("abs-path", re.compile(r"/home/|/Users/|[A-Za-z]:\\|\bC:/"), True),
    ("username", re.compile("|".join(re.escape(u) for u in USERNAMES) or r"(?!)", re.IGNORECASE), True),
    (
        "secret",
        re.compile(
            r"(?i)(?:api[_-]?key|secret|token|passwd|password)\s*[:=]\s*['\"]?[^\s'\",]{8,}"
            r"|\bdb-[A-Za-z0-9]{28,}\b|\bsk-[A-Za-z0-9]{20,}\b|\bghp_[A-Za-z0-9]{30,}\b"
            r"|\bAKIA[0-9A-Z]{16}\b"
        ),
        True,
    ),
    ("account-id", re.compile(r"\b(?:DU|DF|DI|U|F)\d{6,8}\b"), True),
    ("em-dash", re.compile(EM_DASH), True),
]

B64_RUN = re.compile(r"[A-Za-z0-9+/=\n]{200,}")
TEXT_MIMES = ("text/plain", "text/html", "text/markdown", "text/latex", "application/json")


@dataclass(frozen=True)
class Finding:
    path: str
    where: str
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.where}: [{self.rule}] {self.message}"


def _join(src) -> str:
    return "".join(src) if isinstance(src, list) else str(src or "")


def _flatten_html(text: str) -> str:
    """Turn an HTML table into one text line per row so row rules apply."""
    if "<tr" not in text:
        return text
    text = re.sub(r"</t[dh]>\s*", " | ", text)
    text = re.sub(r"</tr>", "\n", text)
    return re.sub(r"<[^>]+>", "", text)


def _scan_text(text: str, path: str, where: str, code: bool = False) -> list[Finding]:
    out: list[Finding] = []
    text = _flatten_html(B64_RUN.sub("", text))
    for i, line in enumerate(text.splitlines(), 1):
        for rule, rx, in_code in LINE_RULES:
            if code and not in_code:
                continue
            m = rx.search(line)
            if m:
                snippet = line.strip()[:70]
                out.append(Finding(path, f"{where}:L{i}", rule, f"matched {m.group(0)[:30]!r} in {snippet!r}"))
    return out


def _scan_notebook(root: Path, p: Path) -> list[Finding]:
    rel = p.relative_to(root).as_posix()
    try:
        nb = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [Finding(rel, "-", "unreadable", f"cannot parse notebook: {exc}")]
    out: list[Finding] = []
    meta = json.dumps(nb.get("metadata", {}))
    out += _scan_text(meta, rel, "metadata", code=True)
    for idx, cell in enumerate(nb.get("cells", [])):
        tag = f"cell{idx}"
        src = _join(cell.get("source"))
        if cell.get("cell_type") == "markdown":
            out += _scan_text(src, rel, f"{tag}.markdown")
            continue
        out += _scan_text(src, rel, f"{tag}.source", code=True)
        for j, o in enumerate(cell.get("outputs", [])):
            where = f"{tag}.out{j}"
            if "text" in o:
                out += _scan_text(_join(o["text"]), rel, where)
            for mime, val in (o.get("data") or {}).items():
                if mime in TEXT_MIMES or mime.startswith("text/"):
                    out += _scan_text(_join(val), rel, f"{where}.{mime}")
                # image/* and other binary mimes are allow-listed
            if o.get("output_type") == "error":
                out += _scan_text("\n".join(o.get("traceback", [])), rel, f"{where}.traceback")
                out += _scan_text(str(o.get("evalue", "")), rel, f"{where}.evalue")
    return out


def _check_gitignore(root: Path) -> list[Finding]:
    gi = root / ".gitignore"
    if not gi.exists():
        return [Finding(".gitignore", "-", "gitignore", "file is missing")]
    lines = {ln.strip() for ln in gi.read_text(encoding="utf-8").splitlines()}
    return [
        Finding(".gitignore", "-", "gitignore", f"missing required pattern {pat!r}")
        for pat in REQUIRED_GITIGNORE
        if pat not in lines
    ]


def _list_files(root: Path) -> list[Path]:
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if Path(top).resolve() == root.resolve():
            res = subprocess.run(
                ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                capture_output=True, check=True,
            )
            names = [n for n in res.stdout.decode("utf-8").split("\0") if n]
            return [root / n for n in names if (root / n).is_file()]
    except (OSError, subprocess.CalledProcessError):
        pass
    files: list[Path] = []
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in p.relative_to(root).parts):
            continue
        if p.is_file():
            files.append(p)
    return files


def scan_repo(root: str | Path) -> list[Finding]:
    root = Path(root)
    findings = _check_gitignore(root)
    for p in sorted(_list_files(root)):
        rel = p.relative_to(root).as_posix()
        name = p.name.lower()
        if any(name.endswith(ext) for ext in DATA_EXTENSIONS):
            findings.append(Finding(rel, "-", "data-file", "data file extension must not be in the repo"))
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > MAX_BYTES:
            findings.append(Finding(rel, "-", "large-file", f"{size / 1e6:.1f} MB exceeds 5 MB"))
            continue
        if name.endswith(".ipynb"):
            findings += _scan_notebook(root, p)
        elif name.endswith(".md"):
            findings += _scan_text(p.read_text(encoding="utf-8", errors="replace"), rel, "md")
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]) if argv else Path(__file__).resolve().parents[1]
    findings = scan_repo(root)
    if findings:
        for f in findings:
            print(f)
        print(f"\npublish gate FAILED: {len(findings)} finding(s)")
        return 1
    print("publish gate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
