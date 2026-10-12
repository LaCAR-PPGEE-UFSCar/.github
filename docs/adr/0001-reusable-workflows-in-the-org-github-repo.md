| Author | Last editor | Last modified |
|---|---|---|
| Guilherme Villela | Guilherme Villela | 2026-10-12 |

# ADR-0001: Lab governance as reusable workflows in the public organization `.github` repository

**Status**: Proposed
**Date**: 2026-10-08
**Deciders**: Guilherme Villela, André Carmona Hernandes

## Context

Two repositories (`educational_aerial_bench`, `event_camera`) carry the same
five workflows and two scripts, copied by hand on 2026-09-28; a fix to one
copy does not reach the other. A third repository
(`tamandua_project_classification`) was created on 2026-10-07 with no
governance at all. The lab head wants automation that is auditable code,
costs nothing, needs nothing installed on his machine, and gives every
repository the same rules with the least effort (brief of 2026-10-07).

## Decision

- The checks are **reusable workflows** (`on: workflow_call`) in the
  organization repository `LaCAR-PPGEE-UFSCar/.github`. Each repository
  calls them from one file, `.github/workflows/governance.yml`, pinned to
  `@main`. Check names are `<job> / check`.
- The repository is **public**: a public kit needs no token for callers to
  read its workflows and scripts, and the same repository serves the default
  PR template, the issue forms and the organization profile. It holds rules
  and templates only, never project data.
- Files that must exist inside each repository (the caller, `CODEOWNERS`,
  the ADR manifest, `CLAUDE.md`, the ADR and runbook templates) come from the
  template repository `LaCAR-PPGEE-UFSCar/lacar_repo_template`; its
  `tools/repo-settings.sh` applies merge strategy, branch protection, labels
  and the project board (amended 2026-10-12: the template replaced the
  `kit/` folder and `tools/adopt.sh` of the first draft).
- Project data (summaries, people, deadlines) never lives here: the lab
  summary goes to the private `LaCAR-PPGEE-UFSCar/lacar_gestao`.

## Alternatives considered

- **Copy the workflows into every repository** — the status quo; drift
  within a month.
- **Private kit with a shared token** — one more secret per repository and
  a reason for the checks to break when it rotates.
- **Organization rulesets with required workflows** — reaches new
  repositories with zero files, but ties the lab to the GitHub Team plan and
  hides the rule from the repository; kept as a later step once the kit is
  stable.

## Consequences

- A change to a check is one PR here and reaches every repository on its
  next PR. A change that adds a required check also needs each repository's
  protection updated (`tools/repo-settings.sh <owner/repo>`).
- Existing repositories migrate by replacing their five workflows with the
  caller and renaming the required contexts.
- Anything in this repository is visible to the public.

## Related

Bench ADR-0001 and ADR-0007 (the rules the kit enforces). Runbooks
`new-repository.md` and `repo-settings.md` of `lacar_repo_template`.
