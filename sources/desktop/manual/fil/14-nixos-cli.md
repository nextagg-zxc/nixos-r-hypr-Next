# NixOS CLI

Karaniwang kinokontrol ang NixOS sa pamamagitan ng mga hotkey at ng menu ng NixOS (`Super + Space`). Ngunit maaari mo rin itong kontrolin sa pamamagitan ng `nixos` CLI. Partikular itong nakakatulong kapag may AI agent kang katrabaho sa pag-customize o pag-configure.

May access ang CLI sa lahat ng internal tooling na ginagamit kapwa sa pamamagitan ng menu at sa iba pang paraan. Makikita mo ang lahat ng available sa pagpapatakbo ng `nixos` sa terminal.

Ganito ang hitsura nito nang halos:

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

At maaari kang sumisid nang mas malalim sa bawat grupo:

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

Tumatanggap din ang bawat command ng `--help`, tanungin mo man ang buong grupo (`nixos capture --help`) o isang command lang (`nixos capture screenshot --help`).

### Pagbubukas ng menu mula sa terminal

Maaari ring i-script ang menu ng NixOS, na madaling gamitin para sa sarili mong mga keybinding. Binubuksan ito ng `nixos menu` sa root, at maaari kang dumiretso sa anumang punto sa tree sa pagbanggit nito: dumidiretso ang `nixos menu summon appearance.theme` sa theme picker, binubuksan ng `nixos menu toggle system` ang system menu at isinasara itong muli kung nakabukas na ito, at itinatago ito ng `nixos menu close`.
