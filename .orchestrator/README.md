# .orchestrator/

This directory holds runtime state for the `mmp` plugin in this repo.

## Files

- `config.yaml` — project-specific configuration for the orchestrator
- `status.yaml` — live state of the current wave (don't edit by hand)
- `<milestone>-context.md` — milestone dossier built by Phase 0
- `infra-brief.md` — repo conventions snapshot for subagents
- `chunks.md` — Phase 1 decomposition output (user-approved)
- `improved-tickets/<id>.{original,draft}.md` — Phase 0.5 audit trail
- `archive/<milestone>-w<N>-<date>/` — completed wave snapshots

## Git tracking policy

The shipped `.gitignore` snippet enforces the following:

| Path | Tracked? | Reason |
|---|---|---|
| `config.yaml` | YES | shared project configuration |
| `README.md` | YES | this file |
| `archive/` | YES | historical wave snapshots — useful for audit |
| `improved-tickets/*.original.md` | YES | disaster-recovery backups of upstream tickets |
| `improved-tickets/*.draft.md` | NO | regenerable per-run scratch |
| `status.yaml` | NO | live runtime state, single-machine |
| `<milestone>-context.md` | NO | regenerable per-run snapshot |
| `infra-brief.md` | NO | regenerable per-run snapshot |
| `chunks.md` | NO | regenerable per-run snapshot |
| `status.yaml.bak` / tmp files | NO | atomic-write artifacts |

If you need to share runtime state across machines, override the snippet
manually — but note that `mmp` assumes a single-user / single-machine
workflow.

## Recovering from a crash

Run `/mmp:doctor` to see where things stand, then `/mmp:resume` (or
`/mmp:run <milestone> --resume`).

## Manual cleanup

`/mmp:archive <milestone>` archives a completed wave. Delete `.orchestrator/`
entirely to start fresh — but ensure no PRs are still open referencing
worktrees that will be removed.
