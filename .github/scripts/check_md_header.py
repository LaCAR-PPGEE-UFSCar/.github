#!/usr/bin/env python3
"""
@file check_md_header.py
@author Guilherme Villela (villela.guilherme@usp.br)
@brief Fail when a Markdown file changed in a PR lacks the header table or was not re-dated.

Usage: check_md_header.py <base_sha> <head_sha>
For every .md added or modified between base and head, the first 6 lines
must contain the table "| Author | Last editor | Last modified |" followed
by a data row whose date (YYYY-MM-DD) is not older than the last commit of
the branch that edited that file (author date, merge commits skipped). Author
dates survive a rebase and an update from develop, so neither of them asks
for a new date: only an edit does. Rule 10 of the coding standard in CLAUDE.md.
Templates pasted into PR/issue bodies and the organization profile README are exempt.
@version 0.4
@date 2026-10-13

@copyright Copyright (c) 2026
"""
import re
import subprocess
import sys

HEADER = re.compile(r"^\|\s*Author\s*\|\s*Last editor\s*\|\s*Last modified\s*\|\s*$", re.I)
ROW = re.compile(r"^\|\s*(?P<author>[^|]+?)\s*\|\s*(?P<editor>[^|]+?)\s*\|\s*(?P<date>\d{4}-\d{2}-\d{2})\s*\|\s*$")


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def main(base, head):
    merge_base = git("merge-base", base, head)
    floor = git("log", "-1", "--format=%cs", merge_base)
    changed = git("diff", "--name-only", "--diff-filter=AM", f"{merge_base}..{head}").splitlines()
    failures = []
    # GitHub templates are pasted into PR and issue bodies, so they carry no header table.
    templates = (".github/pull_request_template.md", ".github/ISSUE_TEMPLATE/", "profile/README.md")
    for path in (p for p in changed if p.endswith(".md") and not p.startswith(templates)):
        with open(path, encoding="utf-8") as fh:
            head_lines = [next(fh, "") for _ in range(6)]
        idx = next((i for i, l in enumerate(head_lines) if HEADER.match(l)), None)
        if idx is None or idx + 2 >= len(head_lines):
            failures.append(f"{path}: header table missing in the first lines")
            continue
        m = ROW.match(head_lines[idx + 2])
        if not m:
            failures.append(f"{path}: data row must be | author | last editor | YYYY-MM-DD |")
            continue
        if not m.group("author").strip() or not m.group("editor").strip():
            failures.append(f"{path}: author and last editor cannot be empty")
            continue
        edited = git("log", "-1", "--no-merges", "--format=%as", f"{merge_base}..{head}", "--", path) or floor
        if m.group("date") < edited:
            failures.append(f"{path}: Last modified {m.group('date')} is older than its last edit on this branch ({edited}); update it")
    for f in failures:
        print(f"::error::{f}")
    print(f"checked {sum(p.endswith('.md') and not p.startswith(templates) for p in changed)} markdown file(s), {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
