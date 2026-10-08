@RTK.md
@/Users/nut/.claude/plugins/marketplaces/karpathy-skills/skills/karpathy-guidelines/SKILL.md

## Research Before Fixing

For infra, networking, CNI, OS-level, or third-party tool problems: run WebSearch before proposing any fix. Known bugs and upstream issues often have cleaner documented solutions than first-principles reasoning. Reading files and checking state is fine first — but search before committing to an approach.

## Auto Mode Confirm Gate

Auto mode ON still requires asking before starting implementation. Skip the ask only when user explicitly says "implement" (or clear equivalent go-ahead) — then proceed straight to work.

## Remote Dev Check

Before running a heavy build/install/test/run command (docker build, npm/cargo/go install or build, long test suites, starting a dev server) in any project: check for a live Mutagen sync session first (`mutagen sync list`, or the `remote-dev` skill's `status` subcommand). If one exists for this project, run the command remotely over `ssh`, not locally. If none exists, ask before running locally — offer to set up remote-dev (see the `remote-dev` skill) instead of assuming local execution.

This is a personal workflow preference (local machine + remote VM setup), not a fact about any given project — never write this into a project's own CLAUDE.md.
