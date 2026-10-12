#!/usr/bin/env python3
"""
@file adr_guard.py
@author Guilherme Villela (villela.guilherme@usp.br)
@brief Fail when a PR changes a guarded decision (per .github/adr-guard.yml) without an ADR.

Usage: adr_guard.py <base_sha> <head_sha> <pr_body_file>
For each ADR in the manifest, the PR hits it when a changed file matches one
of its path globs, an added/removed line of a listed file matches one of its
symbol regexes, or a hunk falls inside a listed markdown section. A hit is
satisfied when the PR changes any file under docs/adr/ or its body cites the
hit ADR id (ADR-NNNN). Otherwise the script exits 1 listing the misses.
A repository without the manifest has nothing guarded: exit 0 with a notice.
@version 0.2
@date 2026-09-11

@copyright Copyright (c) 2026
"""
import fnmatch
import os
import re
import subprocess
import sys

import yaml

MANIFEST = ".github/adr-guard.yml"
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def git(*args, check=True):
    return subprocess.run(["git", *args], text=True, capture_output=True, check=check).stdout


def changed_lines(rng, path):
    out = git("diff", rng, "--", path, check=False)
    return [l[1:] for l in out.splitlines() if (l.startswith("+") or l.startswith("-")) and not l.startswith(("+++", "---"))]


def section_range(rev, path, heading):
    """Line range (1-based, inclusive) of a markdown section in a revision, or None."""
    text = git("show", f"{rev}:{path}", check=False)
    if not text:
        return None
    lines = text.splitlines()
    level = len(heading) - len(heading.lstrip("#"))
    start = next((i for i, l in enumerate(lines) if l.strip() == heading), None)
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#" * level + " ") or (level > 1 and lines[j].startswith("#" * (level - 1) + " ")):
            end = j
            break
    return start + 1, end


def hunks(rng, path):
    out = git("diff", "-U0", rng, "--", path, check=False)
    for l in out.splitlines():
        m = HUNK.match(l)
        if m:
            a, b, c, d = (int(x) if x else None for x in m.groups())
            yield (a, a + (b if b is not None else 1) - 1), (c, c + (d if d is not None else 1) - 1)


def overlaps(x, y):
    return x is not None and y is not None and x[0] <= y[1] and y[0] <= x[1] and x[1] >= x[0] and y[1] >= y[0]


def main(base, head, body_file):
    merge_base = git("merge-base", base, head).strip()
    rng = f"{merge_base}..{head}"
    changed = git("diff", "--name-only", rng).splitlines()
    if not os.path.exists(MANIFEST):
        print(f"::notice::{MANIFEST} not found: nothing is guarded in this repository yet")
        return 0
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    with open(body_file, encoding="utf-8", errors="replace") as fh:
        body = fh.read()
    adr_changed = any(p.startswith("docs/adr/") for p in changed)
    cited = set(re.findall(r"ADR-\d{4}", body))

    misses = []
    for adr in manifest.get("adrs", []):
        hits = []
        for pattern in adr.get("paths", []):
            hits += [f"path {p}" for p in changed if fnmatch.fnmatch(p, pattern)]
        for sym in adr.get("symbols", []):
            if sym["file"] in changed:
                lines = changed_lines(rng, sym["file"])
                for pat in sym["patterns"]:
                    rx = re.compile(pat)
                    if any(rx.search(l) for l in lines):
                        hits.append(f"symbol /{pat}/ in {sym['file']}")
        for sec in adr.get("sections", []):
            if sec["file"] in changed:
                old = section_range(merge_base, sec["file"], sec["heading"])
                new = section_range(head, sec["file"], sec["heading"])
                if any(overlaps(o, old) or overlaps(n, new) for o, n in hunks(rng, sec["file"])):
                    hits.append(f"section '{sec['heading']}' of {sec['file']}")
        if not hits:
            continue
        ok = adr_changed or adr["id"] in cited
        status = "ok" if ok else "MISSING ADR"
        print(f"{adr['id']} hit ({status}): " + "; ".join(sorted(set(hits))))
        if not ok:
            misses.append(adr["id"])
    for adr_id in misses:
        print(f"::error::{adr_id} is changed by this PR: add or change a file under docs/adr/ or cite {adr_id} in the PR body")
    if not misses:
        print("adr-guard: no unguarded structural change")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
