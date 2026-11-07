#!/usr/bin/env python3
"""Validate this skills package. See VALIDATION.md.

Never prints matched secret or denylist text: findings show file:line and a
rule id only.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
EXPECTED_SKILLS = ["logic-audit", "pristine-shipping"]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LICENSE_COPYRIGHT = "Copyright (c) 2026 Swarnim Modi"
MIT_BODY = """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

SECRET_RULES = {
    "private-key-block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    "github-token": re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "api-key-sk": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "slack-token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "credential-assignment": re.compile(
        r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"),
    "url-with-credentials": re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"),
    "email-address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "ipv4-address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}
# Inside SKILL.md files only: anything that would make a skill depend on a
# particular machine or on files outside its own folder.
REFERENCE_RULES = {
    "absolute-path": re.compile(r"(?<![\w.:/])/(home|Users|root|etc|var|opt|tmp|mnt|srv)/"),
    "home-path": re.compile(r"(?<![\w])~/"),
    "windows-path": re.compile(r"\b[A-Za-z]:\\"),
    "parent-dir": re.compile(r"\.\./"),
    "file-url": re.compile(r"file://"),
}
MD_LINK = re.compile(r"\]\(([^)\s]+)\)")

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL {msg}")


def ok(msg):
    print(f"PASS {msg}")


def package_files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and ".git" not in p.relative_to(ROOT).parts:
            yield p


def check_frontmatter():
    try:
        import yaml
    except ImportError:
        fail("frontmatter: PyYAML not installed; install it (pip install pyyaml) to parse frontmatter")
        return
    found = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
    if found != EXPECTED_SKILLS:
        fail(f"skills/: expected {EXPECTED_SKILLS}, found {found}")
    for d in found:
        f = SKILLS / d / "SKILL.md"
        rel = f.relative_to(ROOT)
        if not f.is_file():
            fail(f"{rel}: missing")
            continue
        text = f.read_text(encoding="utf-8")
        m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        if not m:
            fail(f"{rel}: no YAML frontmatter block at top of file")
            continue
        try:
            meta = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:
            fail(f"{rel}: frontmatter is not valid YAML ({e.__class__.__name__})")
            continue
        if not isinstance(meta, dict):
            fail(f"{rel}: frontmatter is not a mapping")
            continue
        name, desc = meta.get("name"), meta.get("description")
        errs = []
        if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
            errs.append("name must be lowercase-hyphenated, <=64 chars")
        elif name != d:
            errs.append(f"name '{name}' != folder '{d}'")
        if not isinstance(desc, str) or not desc.strip():
            errs.append("description missing")
        elif len(desc) > 1024:
            errs.append(f"description is {len(desc)} chars (>1024)")
        elif "<" in desc or ">" in desc:
            errs.append("description contains angle brackets")
        extra = set(meta) - {"name", "description"}
        if extra:
            errs.append(f"non-portable keys {sorted(extra)}")
        if not text[m.end():].strip():
            errs.append("empty body")
        for e in errs:
            fail(f"{rel}: {e}")
        if not errs:
            ok(f"{rel}: YAML frontmatter parsed (name={name}, description {len(desc)} chars)")


def check_references():
    for f in sorted(SKILLS.glob("*/SKILL.md")):
        rel = f.relative_to(ROOT)
        bad = 0
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for rule, rx in REFERENCE_RULES.items():
                if rx.search(line):
                    fail(f"{rel}:{n}: {rule}")
                    bad += 1
            for target in MD_LINK.findall(line):
                if re.match(r"[a-z]+:", target) or target.startswith("#"):
                    continue
                if not (f.parent / target.split("#")[0]).resolve().is_relative_to(f.parent) or \
                        not (f.parent / target.split("#")[0]).exists():
                    fail(f"{rel}:{n}: link-outside-or-missing")
                    bad += 1
        if not bad:
            ok(f"{rel}: self-contained (no machine paths, no links outside its folder)")
    # Package-level docs: relative links must resolve inside the repo.
    for f in [ROOT / "README.md", ROOT / "PROVENANCE.md", ROOT / "VALIDATION.md"]:
        rel = f.relative_to(ROOT)
        bad = 0
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for target in MD_LINK.findall(line):
                if re.match(r"[a-z]+:", target) or target.startswith("#"):
                    continue
                t = (f.parent / target.split("#")[0]).resolve()
                if not t.is_relative_to(ROOT) or not t.exists():
                    fail(f"{rel}:{n}: broken-relative-link")
                    bad += 1
        if not bad:
            ok(f"{rel}: relative links resolve inside the repo")


def scan(rules, label):
    hits = 0
    for f in package_files():
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            fail(f"{f.relative_to(ROOT)}: not UTF-8 text")
            continue
        for n, line in enumerate(lines, 1):
            for rule, test in rules.items():
                if test(line):
                    fail(f"{f.relative_to(ROOT)}:{n}: {label}:{rule}")
                    hits += 1
    if not hits:
        ok(f"{label}: no matches in {sum(1 for _ in package_files())} files")


def check_secrets():
    scan({k: (lambda line, rx=rx: bool(rx.search(line))) for k, rx in SECRET_RULES.items()}, "secret-scan")


def check_denylist(path):
    terms = [t.strip().lower() for t in Path(path).read_text(encoding="utf-8").splitlines()
             if t.strip() and not t.startswith("#")]
    rules = {f"entry-{i + 1}": (lambda line, t=t: t in line.lower()) for i, t in enumerate(terms)}
    print(f"INFO denylist: {len(terms)} entries loaded (terms not printed)")
    scan(rules, "denylist")


def check_license():
    before = len(failures)
    lic = ROOT / "LICENSE"
    others = [n for n in ["LICENSE.md", "LICENSE.txt", "COPYING"] if (ROOT / n).exists()]
    if others:
        fail(f"license: extra license files {others}")
    if not lic.is_file():
        fail("license: LICENSE file missing")
    else:
        words = lic.read_text(encoding="utf-8").split()
        expected = ["MIT", "License"] + LICENSE_COPYRIGHT.split() + MIT_BODY.split()
        if words != expected:
            fail(f"license: LICENSE is not the canonical MIT text with '{LICENSE_COPYRIGHT}'")
    for n in ["README.md", "PROVENANCE.md"]:
        text = (ROOT / n).read_text(encoding="utf-8")
        if "MIT" not in text or "(LICENSE)" not in text:
            fail(f"license: {n} does not name MIT and link LICENSE")
        if "not licensed" in text.lower():
            fail(f"license: {n} still carries draft not-licensed wording")
    if len(failures) == before:
        ok(f"license: canonical MIT LICENSE ({LICENSE_COPYRIGHT}); README and PROVENANCE link it")


def readme_install_spec():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    snip = re.search(r"<!-- install-snippet:start -->\s*```bash\n(.*?)```\s*<!-- install-snippet:end -->",
                     readme, re.S)
    dests = re.search(r"<!-- install-dests:start -->(.*?)<!-- install-dests:end -->", readme, re.S)
    if not snip or not dests:
        return None, []
    table = dests.group(1).split("| --- |", 1)[-1].split("\n", 1)[-1]  # body rows after the separator
    rows = [r for r in table.splitlines() if r.startswith("|")]
    found = []
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        m = re.fullmatch(r"`([^`]+)`", cells[2]) if len(cells) > 2 else None
        if m:
            found.append((cells[0], cells[1], m.group(1)))
    return snip.group(1), found


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_snippet(snippet, dest, home, project):
    env = {"HOME": str(home), "PATH": "/usr/local/bin:/usr/bin:/bin", "SKILLS_SRC": str(SKILLS)}
    script = f"set -eu\ndest={dest}\n{snippet}"
    return subprocess.run(["bash", "-c", script], cwd=project, env=env,
                          capture_output=True, text=True, timeout=60)


def check_install():
    snippet, dests = readme_install_spec()
    if not snippet or len(dests) != 6:
        fail("install-test: README install snippet or destination table not found")
        return
    src = {s: sha(SKILLS / s / "SKILL.md") for s in EXPECTED_SKILLS}
    for agent, scope, dest in dests:
        label = f"install-test [{agent}, {scope}, dest={dest}]"
        with tempfile.TemporaryDirectory(prefix="cas-install-") as tmp:
            home, project = Path(tmp, "home"), Path(tmp, "project")
            home.mkdir()
            project.mkdir()
            base = home / dest[2:] if dest.startswith("~/") else project / dest
            r = run_snippet(snippet, dest, home, project)
            if r.returncode != 0:
                fail(f"{label}: exit {r.returncode}: {r.stderr.strip()[:200]}")
                continue
            errs = [s for s in EXPECTED_SKILLS
                    if not (base / s / "SKILL.md").is_file() or sha(base / s / "SKILL.md") != src[s]]
            outside = [p for p in Path(tmp).rglob("*") if p.is_file()
                       and not p.resolve().is_relative_to(base.resolve())]
            if errs:
                fail(f"{label}: not installed byte-identical: {errs}; stray_files={len(outside)}")
                continue
            # Re-run over a modified existing copy: it must be skipped, not overwritten.
            marker = base / "logic-audit" / "SKILL.md"
            marker.write_text("local edit\n")
            r2 = run_snippet(snippet, dest, home, project)
            kept = marker.read_text() == "local edit\n" and "skipped" in r2.stdout and r2.returncode == 0
            if outside or not kept:
                fail(f"{label}: stray_files={len(outside)} no_overwrite={kept}")
            else:
                ok(f"{label}: both skills byte-identical at {base.relative_to(tmp)}; rerun skipped existing copy")
        check_symlinks_kept(snippet, dest, label)


def check_symlinks_kept(snippet, dest, label):
    """Existing symlinks at the destination, broken or live, must be left alone."""
    with tempfile.TemporaryDirectory(prefix="cas-symlink-") as tmp:
        home, project = Path(tmp, "home"), Path(tmp, "project")
        home.mkdir()
        project.mkdir()
        base = home / dest[2:] if dest.startswith("~/") else project / dest
        base.mkdir(parents=True)
        dangling = Path(tmp, "elsewhere", "missing")          # parent does not exist
        live = Path(tmp, "other-skill")
        live.mkdir()
        (live / "SKILL.md").write_text("someone else's skill\n")
        (base / "logic-audit").symlink_to(dangling)
        (base / "pristine-shipping").symlink_to(live)
        r = run_snippet(snippet, dest, home, project)
        kept = (r.returncode == 0
                and r.stdout.count("skipped") == 2
                and (base / "logic-audit").is_symlink()
                and os.readlink(base / "logic-audit") == str(dangling)
                and not dangling.parent.exists()
                and (base / "pristine-shipping").is_symlink()
                and os.readlink(base / "pristine-shipping") == str(live)
                and sorted(p.name for p in live.iterdir()) == ["SKILL.md"]
                and (live / "SKILL.md").read_text() == "someone else's skill\n")
        if kept:
            ok(f"{label}: broken and live symlinks at destination skipped, targets untouched")
        else:
            fail(f"{label}: existing symlink was followed or replaced (exit {r.returncode})")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--denylist", help="file of extra terms to flag, one per line (keep it outside the repo)")
    ap.add_argument("--install-test", action="store_true",
                    help="run the README install snippet in throwaway HOME and project dirs")
    a = ap.parse_args()
    check_frontmatter()
    check_references()
    check_secrets()
    if a.denylist:
        check_denylist(a.denylist)
    check_license()
    if a.install_test:
        check_install()
    print(f"\n{'FAILED' if failures else 'OK'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
