---
name: nixos
description: >
  REQUIRED for end-user customization of Linux desktop, window manager, or system config.
  Use when editing ANY file in ~/.config/, ~/.config/hypr/, ~/.config/nixos/,
  ~/.config/alacritty/, ~/.config/foot/, ~/.config/kitty/, or ~/.config/ghostty/.
  Triggers: Hyprland, window rules, window behavior, animations, keybindings, monitors, gaps, borders,
  blur, opacity, nixos-shell, bar, widgets, terminal config, themes, fonts, background,
  night light, idle, lock screen, screenshots, screen recording, reminders, layer rules, workspace
  settings, display config, appearance changes, and user-facing nixos commands. Excludes NixOS
  source development through `nixos dev link` workflows.
---

# NixOS Skill

Manage [NixOS](https://omarchy.org/) Linux systems - a beautiful, fun, agentic Arch Linux distribution with Hyprland.

This skill is for end-user customization on installed systems.
It is not for contributing to NixOS source code.

## Topic Guides

Deeper instructions for common areas live next to this file. Read the
matching guide before starting:

- [`hyprland.md`](hyprland.md) - keybindings, monitors, window rules, and other Hyprland config
- [`plugins.md`](plugins.md) - the NixOS shell: bar layout, widgets, plugins, idle behavior
- [`theming.md`](theming.md) - themes, backgrounds, and fonts
- [`hooks.md`](hooks.md) - automation hooks that run on system events
- [`capture.md`](capture.md) - screenshots, screen recordings, OCR text capture, and file sharing
- [`contributing.md`](contributing.md) - reporting NixOS bugs and submitting fixes upstream

## Critical Safety Rules

For privileged commands, follow the Privilege Escalation rules below: `sudo` when a terminal is available for the password prompt, `pkexec` when it is not. Do not wrap commands that already manage privilege elevation themselves.

**For end-user customization tasks, NEVER modify anything in `/usr/share/nixos/`** - but READING is safe and encouraged.

This directory is owned by the nixos package. Any local changes will be
overwritten on the next `nixos update`.

```
/usr/share/nixos/     # READ-ONLY - NEVER EDIT (reading is OK)
├── bin/                    # Command source (packaged binaries are on PATH)
├── config/                 # Default config templates
├── themes/                 # Stock themes
├── default/                # System defaults
├── shell/                  # NixOS shell source and defaults
├── migrations/             # Update migrations
└── install/                # Installation scripts
```

**Reading `/usr/share/nixos/` is SAFE and useful** - do it freely to:
- Understand how nixos commands work: `nixos theme set --help` or `cat $(which nixos-theme-set)`
- See default configs before customizing: `cat "$NIXOS_PATH/config/nixos/shell.json"`
- Check stock theme files to copy for customization
- Reference default hyprland settings: `cat /usr/share/nixos/default/hypr/*`

**Always use these safe locations instead:**
- `~/.config/` - User configuration (safe to edit)
- `~/.config/nixos/themes/<custom-name>/` - Custom themes
- `~/.config/nixos/hooks/` - Custom automation hooks

If the request is to develop NixOS itself, this skill is out of scope. Follow repository development instructions instead of this skill.

## Privilege Escalation

For an interactive script or command run in a visible terminal, use `sudo` for
privileged work. NixOS may grant passwordless `sudo` access to particular
commands, and the terminal is the appropriate place to request a password
when one is needed.

Use `pkexec` only when the caller cannot interact with a terminal or cannot
enter a password there, such as a command launched by an agent or a graphical
background process. Do not replace `sudo` with `pkexec` merely because a
command changes system state.

## System Architecture

NixOS is built on:

| Component | Purpose | Config Location |
|-----------|---------|-----------------|
| **Arch Linux** | Base OS | `/etc/`, `~/.config/` |
| **Hyprland** | Wayland compositor/WM | `~/.config/hypr/` |
| **NixOS shell** | Status bar + notifications (Quickshell) | `~/.config/nixos/shell.json` |
| **Launcher/menus** | Quickshell menu | `~/.config/nixos/extensions/nixos-menu.jsonc` |
| **Alacritty/Foot/Kitty/Ghostty** | Terminals | `~/.config/<terminal>/` |
| **NixOS OSD** | On-screen display | Quickshell plugin |

## Command Discovery

NixOS ships a single `nixos` CLI that dispatches to all `nixos-*` binaries via `nixos <group> <action>`. Always prefer this form — it is self-documenting and stable. The underlying `nixos-*` binaries still exist on `PATH` and remain safe to read for source.

```bash
# List every documented command and its summary (--all includes hidden commands)
nixos commands

# Show the commands inside a group
nixos theme --help
nixos refresh --help
nixos restart --help

# Show help for a specific command (does not execute it)
nixos theme set --help

# Machine-readable listing (binary, route, summary, args, aliases)
nixos commands --json

# Read a command's source to understand it
cat $(which nixos-theme-set)
```

### Command Groups

Run `nixos --help` for the full list. The most common groups:

| Group | Purpose | Example |
|-------|---------|---------|
| `nixos refresh` | Reset config to defaults (backs up first) | `nixos refresh shell` |
| `nixos restart` | Restart a service/app | `nixos restart shell` |
| `nixos toggle` | Toggle feature on/off | `nixos toggle nightlight` |
| `nixos theme` | Theme management | `nixos theme set <name>` |
| `nixos bar` | Bar layout and widgets | `nixos bar move nixos.clock --section right` |
| `nixos plugin` | Manage/clone shell plugins | `nixos plugin clone nixos.clock` |
| `nixos hook` | Install automation hooks | `nixos hook install theme-set <script>` |
| `nixos install` | Install optional software / packages | `nixos install docker dbs` |
| `nixos launch` | Launch apps | `nixos launch browser` |
| `nixos capture` | Screenshots and recordings | `nixos capture screenshot` |
| `nixos reminder` | Desktop notification reminders | `nixos reminder 15 "Pickup Jack"` |
| `nixos pkg` | Package management | `nixos pkg add <pkg>` |
| `nixos setup` | Interactive setup wizards | `nixos setup security fingerprint` |
| `nixos update` | System updates | `nixos update` |

## Configuration Locations

Hyprland config lives in `~/.config/hypr/` — see [`hyprland.md`](hyprland.md).
The NixOS shell (bar, notifications, plugins, idle) is configured in
`~/.config/nixos/shell.json` — see [`plugins.md`](plugins.md).

### Terminals

```
~/.config/alacritty/alacritty.toml
~/.config/foot/foot.ini
~/.config/kitty/kitty.conf
~/.config/ghostty/config
```

**Command:** `nixos restart terminal`

### Other Configs

| App | Location |
|-----|----------|
| btop | `~/.config/btop/btop.conf` |
| fastfetch | `/etc/fastfetch/config.jsonc` default; `~/.config/fastfetch/config.jsonc` user override |
| lazygit | `~/.config/lazygit/config.yml` |
| starship | `~/.config/starship.toml` |
| git | `~/.config/git/config` |

## Safe Customization Patterns

### Edit User Config Directly

For simple changes, edit files in `~/.config/`:

```bash
# 1. Read current config
cat ~/.config/hypr/bindings.lua

# 2. Backup before changes
cp ~/.config/hypr/bindings.lua ~/.config/hypr/bindings.lua.bak.$(date +%s)

# 3. Make changes with Edit tool

# 4. Apply changes
# - Hyprland: auto-reloads on save, but MUST validate with `hyprctl reload` and `hyprctl configerrors`
# - NixOS shell: shell.json and user plugin code under ~/.config/nixos/plugins/ hot-reload on save
# - Menus/launcher: ~/.config/nixos/extensions/nixos-menu.jsonc hot-reloads on save
# - Terminals: apply with `nixos restart terminal` (reloads running terminals; foot picks changes up in new windows)
```

### Reset to Defaults -- ALWAYS SEEK USER CONFIRMATION BEFORE RUNNING

When customizations go wrong:

```bash
# Reset specific config (creates backup automatically)
nixos refresh shell
nixos refresh hyprland

# The refresh command:
# 1. Backs up current config with timestamp
# 2. Copies default from $NIXOS_PATH/config/
# 3. Restarts the component where the refresh needs it (e.g. `refresh shell`)
```

## System Commands

```bash
nixos update                  # Full system update
nixos version                 # Show NixOS version
nixos debug --no-sudo --print # Debug info (ALWAYS use these flags)
nixos system lock             # Lock screen
nixos system shutdown         # Shutdown
nixos system reboot           # Reboot
```

**IMPORTANT:** Always run `nixos debug` with `--no-sudo --print` flags to avoid interactive sudo prompts that will hang the terminal.

## Troubleshooting

```bash
# Get debug information (ALWAYS use these flags to avoid interactive prompts)
nixos debug --no-sudo --print

# Reset specific config to defaults
nixos refresh <app>

# Refresh specific config file
# config-file path is relative to ~/.config/
# eg. `nixos refresh config hypr/hyprland.lua` will refresh ~/.config/hypr/hyprland.lua
nixos refresh config <config-file>

# Full reinstall of configs (nuclear option)
nixos reinstall
```

## Decision Framework

When user requests system changes:

1. **Is it a stock nixos command?** Use it directly
2. **Is it a config edit?** Edit in `~/.config/`, never `/usr/share/nixos/`
3. **Is it a theme customization?** Follow [`theming.md`](theming.md); create a NEW custom theme directory
4. **Is it automation?** Follow [`hooks.md`](hooks.md); use `nixos hook install` and the hook `.d` directories
5. **Is it a package install?** Use `nixos pkg add <pkgs...>` (or `nixos pkg aur add <pkgs...>` for AUR-only packages)
6. **Is it built-in shell/plugin code?** Follow [`plugins.md`](plugins.md); clone it with `nixos plugin clone`, never edit the packaged copy
7. **Unsure if command exists?** Run `nixos commands` (or `nixos <group> --help` for one group)

### Reminder Requests

When the user asks to set a reminder, use `nixos reminder <minutes> [message]` directly. Convert natural language durations to minutes and title-case short reminder labels when appropriate.

```bash
nixos reminder 15 "Pickup Jack"
nixos reminder 60 "Check laundry"
nixos reminder show
nixos reminder clear
```

## Out of Scope

This skill intentionally does not cover NixOS source development. Do not use this skill for:
- Editing files in `/usr/share/nixos/` (`bin/`, `config/`, `default/`, `shell/`, `themes/`, `migrations/`, etc.)
- Creating or editing migrations
- Running `nixos dev ...` commands

## Example Requests

- "Change my theme to catppuccin" -> `nixos theme set catppuccin`
- "Add a keybinding for Super+E to open file manager" -> Check existing bindings first, then use `o.rebind` to replace one or `o.bind` to add one in `~/.config/hypr/bindings.lua`
- "Configure my external monitor" -> Edit `~/.config/hypr/monitors.lua`
- "Make the window gaps smaller" -> Edit `~/.config/hypr/looknfeel.lua`
- "Turn on night light" -> `nixos toggle nightlight` (for time-based schedules, edit `~/.config/hypr/hyprsunset.conf` profiles, then `nixos restart hyprsunset`)
- "Set a reminder to pickup jack in 15 minutes" -> `nixos reminder 15 "Pickup Jack"`
- "Show my reminders" -> `nixos reminder show`
- "Clear all reminders" -> `nixos reminder clear`
- "Customize the catppuccin theme colors" -> Overlay: put an edited `colors.toml` in `~/.config/nixos/themes/catppuccin/`, then re-apply the theme (see `theming.md`)
- "Run a script every time I change themes" -> Install it with `nixos hook install theme-set <script>`
- "Change how workspace labels are rendered" -> Clone `nixos.workspaces`, which switches the bar to `<username>.workspaces`, then edit the clone
- "Lock after ten minutes" -> Set `idle.lock` to `600` in `~/.config/nixos/shell.json`
- "Reset shell/bar to defaults" -> `nixos refresh shell`
- "Record my screen" -> `nixos screenrecord --fullscreen`, then `nixos screenrecord --stop-recording` (see `capture.md`)
- "Report this bug to NixOS" -> Gather diagnostics and a capture of the problem, then file it (see `contributing.md`)
