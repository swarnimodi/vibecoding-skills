---
name: pristine-shipping
description: Use when doing non-trivial software work — implementing features, fixing bugs, rewriting calculation or data pipelines, changing code that reads or writes a database, or deciding whether a change is ready to ship. Also use before "fixing" existing behavior, testing a risky change, or claiming work is done.
---

# Pristine Shipping

The bar for calling work done is "proven, with evidence someone else can
check", not "tests pass". This skill does not make code error-free. It makes
the verification thorough and the claims about it honest. Apply these methods
on any project without being asked. The user's and the project's own
instructions take precedence over this file.

## Permission gates: never on your own

- **Never commit, push, merge, deploy, release, run migrations, change shared
  infrastructure or configuration, or touch production without the user's
  explicit go for that specific step.** Approval for one step does not extend
  to the next.
- **Never copy production data or secrets** into test environments, fixtures,
  logs, screenshots or prompts. Use synthetic data, or redacted data the user
  has approved for the purpose.
- Before an approved destructive operation, take a backup and say how to
  restore it. Enter data through the application's real path, not raw writes.

## Working style

- If your agent can run subagents or parallel workers, use them for
  independent exploration, review and test suites, within the environment's
  concurrency limits. A subagent's report is a lead, not verification:
  re-verify load-bearing claims yourself before acting on them.
- **One writer per repository.** Only the coordinating session commits, pushes
  or merges, and only with permission. Before any push or release, fetch and
  compare against the remote; another session may have moved it.
- Don't leave plans or specs that contradict the code. Once a plan is built,
  update or remove it following the project's convention.

## Before changing anything

- **Judge intent first.** Read enough surrounding code to tell a bug from a
  deliberate design choice. If it looks intentional, say so and explain why
  instead of silently "fixing" it. A deliberately open path (an API without a
  guard the UI has) may exist on purpose; ask before closing it.
- **Explain in plain terms before implementing:** current behavior, why it is
  wrong (or intended), what the change does. If there are several
  interpretations, present them; don't pick one silently.
- **Trace downstream.** Follow every change to its callers and dependents;
  build or typecheck after each step. Keep diffs surgical: every changed line
  traces to the request.
- Verify "already done" claims against commits, code or data, never from
  memory or docs alone.

## Testing any feature

- **Be creative.** Invent weird-but-real inputs, orderings, states and user
  behavior. The happy path proves little.
- **Always test several edge cases:** empty and zero, boundary values,
  duplicates, out-of-order sequences, deletes and undo, rejection paths. One
  passing case is not "tested".
- This applies to every kind of feature: UI, scripts, pure logic,
  integrations, not just data pipelines.

## Verifying a big or risky change: the ladder

Climb the full ladder when the change touches calculation or derived-data
logic, or writes persistent data. UI-only changes: rungs 1 and 6. Everything
else: rungs 1 and 2 plus the edge-case testing above.

1. **Build and typecheck clean;** lint at or better than the pre-change
   baseline (measure before and after).
2. **Hand-computed scenarios** for core logic. Derive expected values by hand,
   never by copying the code's own output.
3. **Isolated data environment.** If a data store is involved, test against a
   disposable, non-production instance the project already supports (a local
   or containerized instance, a test or branch database) seeded with
   synthetic or approved redacted data. Never test against production or a
   shared environment others depend on. If no isolated environment exists,
   don't create infrastructure without permission; say which rungs could not
   be climbed. Drive tests through the real application or API path, the
   same flows a user hits. Direct database access is for asserting state and
   for deliberate corruption tests only.
4. **Edge-case suite with weird-but-real synthetic data:** out-of-order entry,
   same-moment orderings, boundary dates, deletes of the oldest, middle and
   newest rows, duplicates, empty states, rejections. Hand-computed full
   expected result sets. Keep the suite and rerun it after any change to the
   logic it covers.
5. **Chaos phase.** Seeded randomized runs (print the seed so any failure can
   be replayed) that simulate messy real usage: wrong data entered, noticed
   later, fixed through edits, deletes and backdated inserts. Check results
   against an **independent oracle**: expectations recomputed from the input
   log by separate code, never by calling the code under test. Not
   calculation-only: list filters, "latest row" wiring and other plumbing
   still get a seeded run.
6. **Real UI walkthrough** of any interface the change touches, using the
   browser automation available in your environment, or written steps the
   user can follow if none is. Do this last, after implementation is
   complete; screenshots of half-built UI prove nothing. Judge the
   screenshots on two questions: does it look right, and can a user actually
   complete the flow (row actions, dialogs, errors, not just the first
   render)? Code that works but is awkward to use is not done.
7. **Differential check** when rewriting derived data: new output must match
   independently verified reference output exactly.

**Test hygiene:** assert full result sets in both directions (missing and
extra rows both fail); rejected operations must leave state unchanged, so
assert it; prove each test can fail (a negative control or deliberate
corruption); review the test suite itself adversarially; restore everything
afterwards (flags, servers, test rows).

## Claiming work: leftovers are work

- **Say what you did not climb.** If the chaos phase did not run, a role or
  UI path was skipped, or a sibling screen has the same problem, list it as
  "not claimed" with the reason. Don't bury it under the happy path.
- **Same class of bug, different place.** Fixing an unbounded fetch on one
  endpoint does not fix another unbounded fetch elsewhere. Name it or fix it.
- **A missing fixture is not a skip.** No test user or empty-state record?
  Create a throwaway through the real application path in the isolated
  environment, using the test accounts and sessions that environment
  provides, walk the path, then remove it. Never mint credentials or sessions
  for real users or for production.
- **"Tested from all angles" is a scoped claim.** List the rungs you climbed
  and the ones you did not. A precise boundary is acceptable; a flattering
  one is not.
- **Be exact about limits.** Asked "what's the limit?", give the UI page size,
  the server-side cap, and any unbounded fetches you did not touch. "We
  paginate now" is not an answer.
- **Don't overclaim the abstraction.** A filter on creation time is not "data
  as of any past date" unless you built that. Name the exact key used.

## Shipping risky changes

- **Verification earns the release; release mechanics don't replace it.**
  Climb the ladder before release, whatever the rollout strategy.
- **Follow the project's release policy.** Feature flags, canaries, staged or
  percentage rollouts and shadow runs are legitimate risk controls. Propose
  them where they reduce risk and say what each stage proves, but never use
  them in place of verification you could have done beforehand.
- **Keep rollback cheap.** Prefer small, revertable changes; avoid
  irreversible schema changes where possible; know the rollback path before
  asking for the release.
- If the ladder cannot be climbed for some change, say so and raise it with
  the user.

## Communication

- Lead with the outcome. Order findings by severity, critical first. Use a
  table for anything likely to be forwarded.
- Report failures plainly, with their output. Never claim done without fresh
  evidence: run the checks now, after the last change. "I verified it earlier
  in the session" does not count.
- **Fixed is not released.** State the branch, the commit if there is one,
  and whether it is live.
- When the user corrects you, apply the correction for the rest of the work.
  If they want it kept, record it where they keep durable project
  instructions; don't create memory stores on your own.
