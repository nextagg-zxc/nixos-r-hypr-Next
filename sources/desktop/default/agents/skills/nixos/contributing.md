# Reporting Issues and Submitting PRs

Read this when the user wants to report an NixOS bug, suggest a feature, or
contribute a fix upstream.

NixOS lives at https://github.com/omacom/omarchy. Route requests to the
right place:

- **Verified bugs** -> GitHub issues. Issues are for validated bugs only, not
  support requests.
- **Feature ideas and suggestions** ->
  https://github.com/omacom/omarchy/discussions/categories/suggestions
- **Support and "is this a bug?" questions** -> the Discord community at
  https://omarchy.org/discord. Start here when the problem isn't clearly a bug
  in NixOS itself.

## Filing a Good Bug Report

The bug template asks for system details (CPU, GPU, NixOS version), a
description with steps to reproduce, and diagnostics. Gather them:

```bash
nixos version

# Generate the diagnostic log (also written to /tmp/nixos-debug.log)
nixos debug --no-sudo --print

# Interactive variant: `nixos debug` offers to upload the log to
# logs.nixos.org (expires after 24h) and prints a shareable URL to
# include in the issue.
```

**Capture the problem on screen.** A screenshot or short recording of the bug
is often worth more than the description — see [`capture.md`](capture.md) for
`nixos capture screenshot` and `nixos screenrecord`. Keep recordings short
and focused on the misbehavior. GitHub issue attachments are added by
drag-and-drop in the web form, so save the capture and hand the user the file
path to attach (`gh` cannot upload media).

For screen-recording failures specifically, rerun with
`NIXOS_SCREENRECORD_DEBUG=true` and attach `$XDG_RUNTIME_DIR/nixos-screenrecord.log` (or `${XDG_STATE_HOME:-$HOME/.local/state}/nixos/nixos-screenrecord.log` without a session runtime directory).

File the issue with `gh` when available:

```bash
gh issue create --repo omacom/nixos --title "..." --body "..."
```

Include: what happened, what was expected, steps to reproduce, system details,
the debug log URL (or attached log), and the capture.

## Submitting a PR

Never develop against `/usr/share/nixos`. Clone a working copy instead:

```bash
gh repo fork omacom/nixos --clone
cd nixos
```

Follow the repository's own `AGENTS.md` for style, testing, and commit
conventions — it is the authority on contributions. Keep commits atomic, run
`./test/all` before pushing, and open the PR with `gh pr create`. A PR that
fixes a visual problem should include before/after captures (again, see
[`capture.md`](capture.md)).
