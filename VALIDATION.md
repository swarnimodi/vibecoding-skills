# Validation

`scripts/validate.py` checks the package. It needs Python 3.9+ and PyYAML
(`pip install pyyaml`); without PyYAML the frontmatter check fails rather
than being skipped. It exits non-zero on any failure.

| Check | What it does |
| --- | --- |
| Frontmatter | Parses each `SKILL.md` frontmatter with a real YAML parser. Requires exactly `name` and `description`; `name` is lowercase-hyphenated, at most 64 characters and equal to its folder name; `description` is non-empty, at most 1024 characters, with no angle brackets; the body is not empty. |
| Self-contained references | In each `SKILL.md`: no absolute paths, no home-directory paths other than the agents' standard config folders (`~/.claude/`, `~/.codex/`), no Windows paths, no `../`, no `file://`, and every relative Markdown link resolves inside the skill's own folder. In the top-level docs, every relative link resolves inside the repository. |
| Secret scan | Every file outside `.git`: private-key blocks, cloud and Git-host tokens, `sk-` style keys, Slack and JWT tokens, quoted credential assignments, URLs with embedded credentials, email addresses and IPv4 addresses. Prints `file:line: rule`, never the matched text. |
| Denylist (`--denylist FILE`) | Flags any line containing a term from `FILE` (case-insensitive, one term per line, `#` comments allowed). Use it for private names, hostnames or tool names that must not appear. Prints the entry number, never the term. Keep the file outside this repository. |
| License | `LICENSE` must be the canonical MIT text (compared word by word) with `Copyright (c) 2026 Swarnim Modi`; no second license file; README and PROVENANCE must name MIT, link `LICENSE`, and carry no leftover "not licensed" draft wording. |
| Install test (`--install-test`) | Extracts the install snippet and the destination table from `README.md`, then for every row runs the snippet with `bash` in a fresh temporary `HOME` and project directory. Passes when both skills land at the documented location byte-identical to the source, nothing is written anywhere else in the temporary tree, a second run skips an existing (locally edited) copy instead of overwriting it, and a run where the destination already holds a broken symlink and a symlink to another folder leaves both symlinks and their targets untouched. Your real `HOME` and installed skills are never touched. |

What it does **not** check: that a given agent version actually discovers
and invokes the skills. Install locations and invocation syntax in the
README come from each vendor's documentation (links there); check them in
your agent with its skill list (`/skills` in Codex, the `/` menu in Claude
Code and Cursor) after installing.
