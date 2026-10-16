# Claude Code repository guide

Read [AGENTS.md](AGENTS.md) before changing runtime behavior and
[CONTRIBUTING.md](CONTRIBUTING.md) before preparing a release. `3d` owns the 3D piece, not the page
around it: 2D scroll and DOM motion, layout scaling, image or video generation and print
orchestration belong to adjacent skills.

Run `scripts/check-sync` after every runtime, script, asset, metadata, documentation or evaluation
change. No `/Users/` paths in shipped files; every rule has one canonical home, so link instead of
restating.
