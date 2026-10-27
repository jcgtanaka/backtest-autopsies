"""Tests for tools/publish_gate.py (written before the gate)."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import publish_gate as pg

GITIGNORE = "\n".join(pg.REQUIRED_GITIGNORE) + "\n"
EM = chr(0x2014)


def make_repo(tmp_path: Path, gitignore: str = GITIGNORE) -> Path:
    (tmp_path / ".gitignore").write_text(gitignore, encoding="utf-8")
    (tmp_path / "README.md").write_text("# Clean readme\n\nNothing here.\n", encoding="utf-8")
    return tmp_path


def write_nb(path: Path, outputs=None, markdown: str = "text", code: str = "x = 1") -> None:
    nb = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [markdown]},
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": 1,
                "source": [code],
                "outputs": outputs or [],
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb), encoding="utf-8")


def stream(text: str) -> list[dict]:
    return [{"output_type": "stream", "name": "stdout", "text": [text]}]


def rules(findings) -> set[str]:
    return {f.rule for f in findings}


def test_clean_repo_passes(tmp_path):
    make_repo(tmp_path)
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", stream("Sharpe 0.12 net -0.18\n"))
    assert pg.scan_repo(tmp_path) == []
    assert pg.main([str(tmp_path)]) == 0


def test_missing_gitignore_pattern_fails(tmp_path):
    make_repo(tmp_path, gitignore="__pycache__/\n")
    found = pg.scan_repo(tmp_path)
    assert "gitignore" in rules(found)
    assert pg.main([str(tmp_path)]) == 1


def test_missing_gitignore_file_fails(tmp_path):
    (tmp_path / "README.md").write_text("ok\n", encoding="utf-8")
    assert "gitignore" in rules(pg.scan_repo(tmp_path))


@pytest.mark.parametrize(
    "text,rule",
    [
        ("   open  high  low\n0  1.1  1.2  1.0\n1  1.1  1.2  1.0\n[5 rows x 3 columns]\n", "dataframe"),
        ("2024-01-02 1.10523 1.10901 1.10211 1.10650\n", "price-row"),
        ("2024-01-02 | 101.25 | 102.50 | 100.75 | 101.80\n", "price-row"),
        ("loaded from " + "/ho" + "me/someone/data.parquet\n", "abs-path"),
        ("loaded from C:" + "\\Users\\x\\data.csv\n", "abs-path"),
        ("api_key = 'example-not-a-secret-value'\n", "secret"),
        ("password: hunter2hunter2\n", "secret"),
        ("token=ghp_" + "a" * 36 + "\n", "secret"),
        ("account DU" + "1234567 is funded\n", "account-id"),
        ("a " + EM + " b\n", "em-dash"),
    ],
)
def test_output_patterns_fail(tmp_path, text, rule):
    make_repo(tmp_path)
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", stream(text))
    assert rule in rules(pg.scan_repo(tmp_path))
    assert pg.main([str(tmp_path)]) == 1


def test_html_table_with_price_rows_fails(tmp_path):
    make_repo(tmp_path)
    html = (
        "<table class=\"dataframe\"><tr><th>2024-01-02</th><td>1.10523</td>"
        "<td>1.10901</td><td>1.10211</td></tr></table>"
    )
    out = [
        {
            "output_type": "execute_result",
            "execution_count": 1,
            "metadata": {},
            "data": {"text/html": [html]},
        }
    ]
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", out)
    assert "price-row" in rules(pg.scan_repo(tmp_path))


def test_summary_table_without_dates_passes(tmp_path):
    make_repo(tmp_path)
    html = "<table class=\"dataframe\"><tr><th>0</th><td>0.5</td><td>0.289</td><td>0.181</td></tr></table>"
    out = [{"output_type": "execute_result", "execution_count": 1, "metadata": {},
            "data": {"text/html": [html], "text/plain": ["0  0.5  0.289  0.181"]}}]
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", out)
    assert pg.scan_repo(tmp_path) == []


def test_base64_image_blob_is_allowed(tmp_path):
    make_repo(tmp_path)
    blob = "iVBORw0KGgo" + ("jos" + "gtAAAA/+=" * 200)
    out = [
        {
            "output_type": "display_data",
            "metadata": {},
            "data": {"image/png": blob, "text/plain": ["<Figure size 640x480>"]},
        }
    ]
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", out)
    assert pg.scan_repo(tmp_path) == []


def test_markdown_cell_and_md_file_are_scanned(tmp_path):
    make_repo(tmp_path)
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", markdown="see " + EM + " here")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text("path /ho" + "me/u/x\n", encoding="utf-8")
    found = pg.scan_repo(tmp_path)
    assert {"em-dash", "abs-path"} <= rules(found)


def test_code_cell_source_path_is_flagged(tmp_path):
    make_repo(tmp_path)
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", code="p = '/ho" + "me/u/data'")
    assert "abs-path" in rules(pg.scan_repo(tmp_path))


def test_large_file_fails(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "big.bin").write_bytes(b"0" * (5 * 1024 * 1024 + 1))
    assert "large-file" in rules(pg.scan_repo(tmp_path))


@pytest.mark.parametrize("name", ["a.parquet", "x.dbn", "x.dbn.zst", "prices.csv", "d.feather"])
def test_data_extension_fails(tmp_path, name):
    make_repo(tmp_path)
    (tmp_path / "somewhere").mkdir()
    (tmp_path / "somewhere" / name).write_bytes(b"x")
    assert "data-file" in rules(pg.scan_repo(tmp_path))


def test_findings_name_file_and_rule(tmp_path):
    make_repo(tmp_path)
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", stream("a " + EM + " b\n"))
    f = pg.scan_repo(tmp_path)[0]
    assert "notebook.ipynb" in str(f)
    assert "em-dash" in str(f)


def test_repo_gitignore_has_data_patterns():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for pattern in ("data/", "*.parquet", "*.dbn", ".env", ".ipynb_checkpoints/", "private/"):
        assert pattern in text, pattern


def test_username_rule_reads_environment(tmp_path, monkeypatch):
    make_repo(tmp_path)
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", stream("user is exampleuser\n"))
    monkeypatch.setenv("PUBLISH_GATE_USERNAMES", "exampleuser")
    importlib.reload(pg)
    try:
        assert "username" in rules(pg.scan_repo(tmp_path))
    finally:
        monkeypatch.delenv("PUBLISH_GATE_USERNAMES")
        importlib.reload(pg)


def test_username_rule_off_without_environment(tmp_path, monkeypatch):
    monkeypatch.delenv("PUBLISH_GATE_USERNAMES", raising=False)
    importlib.reload(pg)
    make_repo(tmp_path)
    write_nb(tmp_path / "cases" / "a" / "notebook.ipynb", stream("user is exampleuser\n"))
    assert "username" not in rules(pg.scan_repo(tmp_path))
