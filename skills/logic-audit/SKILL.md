---
name: logic-audit
description: Project-wide hunt for logical holes, meaning places where the system does not follow its own stated rules on every path. Covers a rule enforced in one place and skipped in another, two places computing the same fact differently, something left behind when a role, membership, event or record ends, features built at different times that never learnt about each other, gated features leaking past their gate, and decided features that were never built. Audit-only by default; fixes need explicit permission. Use when the user asks to find or plug logical holes or loopholes, check that the system is consistent with its rules or decisions, audit business logic, or make sure everything is logically consistent. Also use before launching a feature that touches money, roles, entitlements, flags or deletion.
---

# Logic audit

Find every place where the system's behaviour does not follow, on every
path, a rule the project has stated, or a rule that plainly follows from
the stated ones. Report them. Fix them only when the user says so.

This is not a code review, a style pass, a performance pass or a security
scan, though it finds security and money bugs. Its question is always: **"the
rules say X; is X true everywhere, for everyone, at every point in time?"**

## 0. Mode: audit-only unless told otherwise

- **The default deliverable is a report.** While auditing, do not edit code,
  data, configuration, schemas or docs, and do not commit, push, deploy or
  run migrations.
- **Fixing is a separate, permissioned step.** Start it only after the user
  explicitly approves which findings to fix (see section 7). "Find the holes"
  is not permission to fix them; "find and plug the holes" is permission to
  propose fixes, and anything consequential (data writes, migrations,
  deploys, merges) still needs its own explicit go.
- **Never touch production to prove a hole,** and never copy production data
  or secrets into an audit environment, a report or a prompt.

## 1. Index all the context first (mandatory)

Every audit starts here. Do not hunt for a single hole until this index
exists. An audit that skips it finds holes against rules it guessed.

Read, and list what you read:

- **Agent memory and instruction files:** every CLAUDE.md, AGENTS.md,
  .cursor/rules, memory folder and skill in the project.
- **Written rules and decisions:** docs, ADRs and decision logs, READMEs,
  specs, and comments that state a rule.
- **The code itself:** entry points, routes and handlers, data models and
  schema, migrations, jobs and cron, roles, permissions and flags, and every
  reader and writer of each key entity.

From that index, write two things:

- **A rules inventory:** each stated rule with its source (file:line, or
  "user, date"). It seeds the rules ledger in section 2.
- **An enforcement map:** for each rule, every place it should be enforced.
  The hunt then checks each of those places.

Only then start the audit. Every finding cites its rule's source from this
index; an implied rule cites the stated rules it follows from.

**Name what you could not read.** If some context is missing, unreadable,
too large or off limits, list it as an index gap in the report. Do not guess
what it says.

## 2. Build the rules ledger (the oracle)

You cannot find a hole without the rule it breaks. Collect rules from:

- The project's instruction files: AGENTS.md, CLAUDE.md, README, docs/,
  ADRs, plan and ledger files, and any "decisions" sections.
- The user's decisions: this conversation, issue threads, and any notes the
  user points you to. **The newest decision wins.** Note every place older
  text contradicts it.
- The schema and code: CHECK constraints, policies, comments that state an
  invariant ("only admins may…", "never…", "always…").
- User-facing copy: every promise in the UI or in emails is a rule ("you can
  cancel any time", "free for members").

Write the ledger as one line per rule: the rule, its source (file:line or
"user, date"), and its scope (which entities, roles and paths it covers).
Then add the **implied rules**. "Premium members don't pay for sessions"
implies that every seat counter, payment check, reminder, door list, refund
path and receipt must know about premium. Implied rules are where most holes
hide, because nobody wrote them down.

Accepted exceptions ("by decision", "accepted", "known limitation") are
part of the ledger. They are not holes unless a newer decision overrides
them.

## 3. Map the model

- **Actors.** Include the awkward ones: signed out, anonymous or guest
  session, half-onboarded (applied, invited, unverified), on hold, rejected,
  suspended, demoted, deleted, a system or service account, an admin acting
  on themselves, a background job, a webhook from a third party.
- **Entities and their states.** Draw each state machine, including the
  states nothing ever moves a record out of.
- **Writers.** For each state or field, list every path that writes it: UI
  actions, API routes, webhooks, scheduled and queued jobs, database triggers
  and functions, admin overrides, imports and scripts, and a direct API or
  database write that skips the UI. **Search for writes to the field, not
  for calls to the function you expect.**
- **Readers.** For each derived fact (a count, "is paid", "is open", "who is
  coming", "is a host"), list every place that computes it.

## 4. Hunt: the eight kinds of hole

1. **A rule that is not enforced on every path.** It is enforced on path A
   but a sibling path B reaches the same state without it: another action,
   an admin override, a webhook, a privileged (security-definer or
   service-role) function, a direct API write, a client-only check, a retry.
2. **Readers that disagree.** Two places compute the same fact with
   different predicates, so one page says 8 and another says 0. Put the
   predicates side by side and diff them clause by clause.
3. **Lifecycle gaps.** For each entity and grant, ask what happens when it
   ends, expires, is removed, demoted, deleted, unpublished, renamed,
   re-added or undone. What still acts on it? Look for leftover grants,
   sessions and caches, queued jobs and notifications, badges, counts,
   links, scheduled work, entitlements and free access. Also check the
   reverse: re-granting something silently revives old state.
4. **Features that never learnt about each other.** Make a matrix of
   features built at different times. For each pair, ask whether A's rules
   know about B. Money × roles × entitlements × flags × deletion × time is
   where the worst holes live.
5. **Missing features the rules imply.** A decision with no code. A column
   nothing writes. A status nothing leaves. A button that leads nowhere.
   Copy that promises behaviour nothing performs.
6. **Gates that disagree.** List every surface of a gated or unpublished
   thing: page, title and metadata, navigation, sitemap and robots, API,
   server payload and client bundle, emails, push notifications, background
   jobs, admin counts, search, exports. One open surface is a leak.
7. **Copy that contradicts behaviour.** The UI or an email says one thing
   and the system does another.
8. **Docs that contradict code.** Say which side looks right. Don't assume
   it is the docs.

Cross-cutting checks on every finding's path:

- **Concurrency:** a double submit, two tabs, two admins, a retried webhook,
  events out of order.
- **Time:** time zones, the moment of the boundary ("ends at", "today",
  grace periods), and something that changes between a check and its use.
- **Identity:** never trust a key, id or role the client sends; the server
  must derive who the caller is.
- **Failure:** a failed read must never look like an empty or zero result
  that the system then acts on.

## 5. Verify before reporting

Every finding needs:

- the **rule**, quoted with its source from the index;
- the **hole**, with file:line for each path that breaks it;
- a **concrete scenario**: steps a real person or job could take that hit it;
- a check that it is **not an accepted exception** and not overridden by a
  newer decision;
- **severity**:
  - critical: money moves wrong, data is lost, or private data leaks;
  - high: a stated rule is broken for real users;
  - medium: inconsistent, with limited harm;
  - low: copy or doc drift;
- **confidence**, and what you did not verify.

Where it is safe, reproduce: a test or a query against an isolated,
non-production environment seeded with synthetic data. Read-only queries
against a shared non-production environment need the user's permission.
Never write to production to prove a hole. Speculation you did not trace is
not a finding.

## 6. Fan out when the system is large

If your agent can run subagents or parallel workers, split by domain, for
example roles and access, money and entitlements, the core object's
lifecycle, identity and privacy, public surfaces and flags, and admin
tooling. Give every auditor one shared brief:

- the index, enforcement map, rules ledger and newest decisions;
- the eight kinds;
- what not to report;
- the finding format above;
- the domain's own list of readers, writers and surfaces.

Auditors are **read-only**: no edits, no git writes, no builds, no
servers, no database writes. Each writes its report to a scratch file
outside the project.

**Respect the machine.** If the user or environment sets a concurrency cap,
run auditors in waves no bigger than the cap. Don't run builds or browsers
while a wave is working. Without subagents, audit the domains one at a time
in the same order.

A subagent's report is a lead, not a verdict. Re-verify every finding you
will report or act on, yourself, against the code.

## 7. Report, then fix only with permission

**Report**, in this order:

- **Coverage:** every rule and surface checked, including the ones found
  consistent, so the reader can see what was covered.
- **Index gaps:** every piece of context you could not read, and what that
  leaves unverified.
- **Findings:** ranked by severity.
- **Decisions only the user can take:** a short list, each with a
  recommendation.
- **Proposed fixes:** for each finding, where you would close it and how,
  without applying anything. Then stop and ask which to fix.

**Fix**, once the user has approved specific findings:

- Close the hole at the lowest layer every path passes through: the
  database or service, not the button.
- Don't "fix" something that looks intentional without asking. Say why it
  looks deliberate.
- For money, security, privacy and deletion, add a check that fails on the
  code before the fix (a negative control) and passes after it.
- Update the rules file in the same change, so the next audit's oracle is
  right.
- Rerun the project's own checks and report the results. Committing,
  merging and releasing remain separate decisions for the user.
