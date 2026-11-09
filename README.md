# swarnim-skills

Two portable skills for coding agents. Each is one self-contained
`SKILL.md` with standard YAML frontmatter (`name`, `description`). The skills
themselves need no scripts or dependencies; only the optional validator in
`scripts/` needs Python 3 and PyYAML.

Repository: <https://github.com/swarnimodi/swarnim-skills> (default
branch `main`). License: [MIT](LICENSE).

| Skill | What it does | Default behaviour |
| --- | --- | --- |
| [`pristine-shipping`](skills/pristine-shipping/SKILL.md) | A verification ladder and honest-claims discipline for non-trivial changes: hand-computed scenarios, edge-case and seeded chaos testing against an independent oracle, UI walkthroughs, and scoped "done" claims. | Works on the code it is asked to change. Commits, pushes, merges, deploys, migrations and anything touching production or shared infrastructure need the user's explicit go for each step. Test data is synthetic or approved-redacted, never copied from production. |
| [`logic-audit`](skills/logic-audit/SKILL.md) | A project-wide hunt for places where the system breaks its own stated rules: unenforced paths, disagreeing readers, lifecycle gaps, leaky gates, missing implied features. | **Audit-only.** Produces a report with proposed fixes and stops. Applying fixes needs explicit permission for the specific findings. |

Neither skill can guarantee error-free code or ship anything on its own.

## Install

### 1. Get the skills

Fetch them somewhere outside your project, then point `SKILLS_SRC` at the
`skills/` folder. With git:

```bash
git clone --depth 1 --branch main https://github.com/swarnimodi/swarnim-skills.git
SKILLS_SRC="$PWD/swarnim-skills/skills"
```

Or without git (the archive unpacks to `swarnim-skills-main/`):

```bash
curl -fsSL https://github.com/swarnimodi/swarnim-skills/archive/refs/heads/main.tar.gz | tar -xz
SKILLS_SRC="$PWD/swarnim-skills-main/skills"
```

Single files are also available directly:
[`pristine-shipping/SKILL.md`](https://raw.githubusercontent.com/swarnimodi/swarnim-skills/main/skills/pristine-shipping/SKILL.md),
[`logic-audit/SKILL.md`](https://raw.githubusercontent.com/swarnimodi/swarnim-skills/main/skills/logic-audit/SKILL.md).

### 2. Copy them where your agent looks

Pick a destination from the table below. For a project-level location, `cd`
to your project root first.

```bash
dest=~/.claude/skills    # a location from the table
```

Then run:

<!-- install-snippet:start -->
```bash
mkdir -p "$dest"
for s in logic-audit pristine-shipping; do
  if [ -e "$dest/$s" ] || [ -L "$dest/$s" ]; then
    echo "skipped (already exists, not overwritten): $dest/$s"
  else
    cp -R "$SKILLS_SRC/$s" "$dest/" && echo "installed: $dest/$s"
  fi
done
```
<!-- install-snippet:end -->

The loop never overwrites anything already at the destination path,
including a symlink, even a broken one. If you already have a skill with the
same name, remove or rename it yourself first; agents do not merge
same-named skills.

<!-- install-dests:start -->
| Agent | Scope | `dest` | Invoke explicitly |
| --- | --- | --- | --- |
| Claude Code | personal (all projects) | `~/.claude/skills` | `/logic-audit`, `/pristine-shipping` |
| Claude Code | project | `.claude/skills` | `/logic-audit`, `/pristine-shipping` |
| Codex (CLI / IDE) | user | `~/.agents/skills` | `$logic-audit`, `$pristine-shipping`, or pick from `/skills` |
| Codex (CLI / IDE) | repository | `.agents/skills` | `$logic-audit`, `$pristine-shipping`, or pick from `/skills` |
| Cursor | project | `.cursor/skills` | type `/` in Agent chat and pick the skill |
| Cursor | user | `~/.cursor/skills` | type `/` in Agent chat and pick the skill |
<!-- install-dests:end -->

All three agents also pick a skill automatically when the task matches its
`description`, for example "audit the business logic for holes" or "is this
ready to ship?". Restart the agent if a newly copied skill does not appear.

Notes, from each vendor's documentation (checked 2026-11-07):

- Claude Code: <https://code.claude.com/docs/en/skills>
- Codex: <https://learn.chatgpt.com/docs/build-skills>. Older Codex versions
  read `~/.codex/skills`; current docs list `~/.agents/skills`.
- Cursor: <https://cursor.com/docs/skills>. Cursor also loads
  `.agents/skills`, `.claude/skills`, `.codex/skills` and their home-directory
  equivalents, so a copy installed for Claude Code or Codex may already be
  visible in Cursor. Installing the same skill in two of those places can
  show it twice.

To uninstall, delete the skill's folder from `dest`.

## Agents without native skill support

Any agent that reads an instruction file (`AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, `.github/copilot-instructions.md`, a rules file, and so on) can
load the skills explicitly. Copy the folders into your project (for example
`docs/agent-skills/`) and add to the instruction file:

```markdown
## Skills
- Before non-trivial changes, or before saying work is done or ready to ship,
  read and follow `docs/agent-skills/pristine-shipping/SKILL.md`.
- When asked to audit business logic or find logical holes, read and follow
  `docs/agent-skills/logic-audit/SKILL.md`. It is audit-only unless I
  approve specific fixes.
```

If the agent has no instruction file either, attach or paste the relevant
`SKILL.md` into the conversation and say "follow this skill".

## Validate

From a checkout:

```bash
python3 scripts/validate.py                 # frontmatter, references, secret scan, license check
python3 scripts/validate.py --install-test  # also runs the install snippet above in throwaway HOME and project dirs
python3 scripts/validate.py --denylist FILE # also flag any term listed in FILE (one per line), e.g. private names
```

See [VALIDATION.md](VALIDATION.md) for what each check covers. Keep any
denylist file outside this repository.

## License and provenance

MIT, see [LICENSE](LICENSE). [PROVENANCE.md](PROVENANCE.md) records where the
skills came from and what changed for public release.
