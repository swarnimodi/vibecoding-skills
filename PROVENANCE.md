# Provenance

Both skills are original work by Swarnim Modi, written with the help of AI
coding agents. The author has confirmed that they contain no restricted
third-party content and has released them under the MIT License (see
[LICENSE](LICENSE)).

## Sources

The published files are adapted from the author's personal versions of the
same skills.

| Published file | Adapted from | Source SHA-256 | Source last modified |
| --- | --- | --- | --- |
| `skills/pristine-shipping/SKILL.md` | personal `pristine-shipping` skill | `4c033c77f883210fba756bf52424e37fa951f1c29d73284d7abb58eec0213ac3` | 2026-11-01 |
| `skills/logic-audit/SKILL.md` | personal `logic-audit` skill | `ada19463a1d7b8b3ad033fc5501d6fb577d14d3250563bb141d920c69a66a97d` | 2026-10-21 |

## Changes for public release

- Kept the core method of each skill, mostly in the original wording.
- Removed personal names, machine paths, and dependencies on specific
  browser, memory or agent tooling.
- Testing uses synthetic or approved-redacted data in isolated
  non-production environments; production data and secrets are never copied.
- Consequential operations (commit, push, merge, deploy, migrations,
  production, shared infrastructure) need the user's explicit permission.
- `logic-audit` is audit-only by default; fixes need explicit approval.
- Staged rollouts are allowed as risk controls under the project's release
  policy, but never replace verification before release.
