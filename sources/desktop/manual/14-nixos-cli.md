# NixOS CLI

NixOS is usually controlled through the hotkeys and the NixOS menu (`Super + Space`). But you can also control it through the `nixos` CLI. This is particularly helpful when you're having an AI agent work with you on customization or configuration.

The CLI has access to all the internal tooling that is used both via the menu and otherwise. You can see everything that's available by running `nixos` in the terminal.

It looks something like this:

```
~ ❯ nixos
NixOS command center

Usage:
  nixos <command> [args...]
  nixos commands [--all] [--json] [--check]
  nixos <group> --help
  nixos <group> <command> --help

Common commands:
  nixos update              Update NixOS and system packages
  nixos theme list          List available themes
  nixos theme set <name>    Apply a theme
  nixos font list           List available fonts
  nixos screenshot          Take a screenshot
  nixos debug               Print debugging information

Groups:
  agent          AI coding agents, their usage, and subscription accounts
  audio          Audio input and output controls
  bar            NixOS shell bar layout and settings
  battery        Battery status helpers
  bluetooth      Bluetooth device controls
  branch         NixOS git branch management
  branding       About and screensaver branding
  brightness     Display and keyboard brightness
  capture        Screenshots and screen recording
  channel        NixOS release channel management
  clipboard      Clipboard helpers
  cmd            Command and shortcut helpers
  config         System configuration helpers
  debug          Diagnostics and support logs
  ...
```

And you can dive deeper on every group:

```
~ ❯ nixos capture
Capture commands — Screenshots and screen recording:
  nixos capture qr                                                                                                                                                                                                       Decode a QR code from a screenshot region
  nixos capture screenrecording [--fullscreen] [--with-desktop-audio] [--with-microphone-audio] [--with-webcam] [--webcam-device=<device>] [--webcam-size=<small|medium|large>] [--resolution=<size>] [--stop-recording]  Start or stop screen recording
  nixos capture screenrecording with webcam                                                                                                                                                                              Pick a webcam and start a screen recording with it
  nixos capture screenshot [smart|region|windows|fullscreen|scroll] [copy|save]                                                                                                                                          Take a screenshot
  nixos capture text                                                                                                                                                                                                     Extract text from a screenshot region with OCR
  nixos capture webcam resize <smaller|larger|reset|small|medium|large>                                                                                                                                                  Resize the active webcam recording overlay
```

Every command takes `--help` too, whether you ask a whole group (`nixos capture --help`) or a single command (`nixos capture screenshot --help`).

### Opening the menu from the terminal

The NixOS menu is scriptable as well, which is handy for your own keybindings. `nixos menu` opens it at the root, and you can jump straight to any point in the tree by naming it: `nixos menu summon appearance.theme` goes right to the theme picker, `nixos menu toggle system` opens the system menu and closes it again if it's already up, and `nixos menu close` puts it away.
