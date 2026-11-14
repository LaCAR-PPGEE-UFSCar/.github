| Author | Last editor | Last modified |
|---|---|---|
| Guilherme Villela | Guilherme Villela | 2026-11-09 |

# LaCAR governance kit

One place for the checks every lab repository runs. Each repository calls
them from one file, `.github/workflows/governance.yml`; the logic lives here,
so a fix lands once and reaches every repository on its next PR (ADR-0001).

This repository is public: rules and templates only, never project data.

## What is here

| Path | Role |
|---|---|
| `.github/workflows/*.yml` | Reusable workflows (`on: workflow_call`): `docs-header`, `adr-guard`, `runbook-check`, `pr-stack-guard`, `enforce-pr-source`, `archive-merged-branch`. `governance-self.yml` runs them on this repository's own PRs. |
| `.github/scripts/` | `check_md_header.py` (markdown header table) and `adr_guard.py` (guarded decisions), fetched by the reusable workflows. |
| `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/` | Default PR template and the issue form "Task", for repositories that have none of their own. |
| `profile/README.md` | The organization's public page. |

## Use it

A new repository starts from
[`lacar_repo_template`](https://github.com/LaCAR-PPGEE-UFSCar/lacar_repo_template)
(runbook `docs/runbooks/new-repository.md` there): it brings the caller, the
files each repository keeps (CODEOWNERS, ADR manifest, CLAUDE.md, ADR and
runbook templates) and `tools/repo-settings.sh`, which applies the settings.

The caller, `.github/workflows/governance.yml` of each repository:

```yaml
jobs:
  docs-header:
    if: github.event.action != 'closed'
    uses: LaCAR-PPGEE-UFSCar/.github/.github/workflows/docs-header.yml@main
  # adr-guard, runbook-check, pr-stack-guard (permissions: pull-requests: read),
  # pr-source (base main only), archive (on merge, permissions: contents: write)
```

Check names the protection expects: `docs-header / check`, `adr-guard / check`,
`runbook-check / check`, `pr-stack-guard / check` on `develop`; `main` adds
`pr-source / check`.

`docs-header` is skipped on PRs into `main` (the protection counts a skipped
job as passed): a release range is made of the squash commits on `develop`,
dated when each PR merged, so comparing them with the header dates would fail
every file that waited a day in review. Each file was already checked in its
own PR into `develop`.

## Change a rule

Open a PR into `develop` here; `governance-self.yml` runs the same checks on
it. Callers pin `@main`, so a change reaches the repositories when `develop`
is released into `main`. A new required check also needs each repository's
protection updated (`tools/repo-settings.sh <owner/repo>`).

## Known failures

| Symptom | Cause | Fix |
|---|---|---|
| Caller fails with "workflow was not found" | This repository became private | Keep it public: callers in private repositories read it without a token |
| `docs-header` fails a release PR into `main` with "older than its last edit" | The caller runs a kit older than the skip on `main` (#7) | Release the kit (`develop` → `main`), then re-run the check |
| `docs-header` fails on a template | A `.md` under `.github/ISSUE_TEMPLATE/` or `profile/` gained a header table | Those files are exempt by path; remove the table |
| Protection rejects the context | Check never ran on that branch yet | Merge the caller first, then run `tools/repo-settings.sh` |
