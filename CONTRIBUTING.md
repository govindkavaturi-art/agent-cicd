# Contributing

Contributions are welcome. A few guidelines to make things smoother:

## Before opening a PR
- Open an issue first if you're planning a significant change. Saves time if the direction isn't right.
- Small fixes (typos, docs, obvious bugs) can skip the issue and go straight to PR.

## What's in scope
This template is meant to stay simple and opinionated. Good contributions:
- Fixes to existing workflows or agent scripts
- Documentation improvements
- New sections in SETUP.md that address real setup issues
- Alternative scheduling layer examples (if you wire it up to something other than CueAPI and it works, I'd love to include it)

## What's out of scope
- Wholesale rewrites of the pipeline architecture
- Framework-specific forks (React, Django, etc) — this is meant to be framework-agnostic
- Adding required dependencies beyond what's already here

## PR checklist
- Tests still pass (if you modified agent scripts)
- README and SETUP.md updated if behavior changes
- No new required secrets without explanation
