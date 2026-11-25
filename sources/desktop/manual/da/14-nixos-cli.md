# NixOS CLI

NixOS styres normalt via genvejstasterne og NixOS-menuen (`Super + Space`). Men du kan også styre det via `nixos` CLI'en. Det er særligt nyttigt, når du har en AI-agent til at arbejde sammen med dig om tilpasning eller konfiguration.

CLI'en har adgang til alle de interne værktøjer, der bruges både via menuen og på anden vis. Du kan se alt, hvad der er tilgængeligt, ved at køre `nixos` i terminalen.

Det ser nogenlunde sådan her ud:

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

Og du kan dykke dybere ned i hver gruppe:

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

Alle kommandoer tager også `--help`, uanset om du spørger en hel gruppe (`nixos capture --help`) eller en enkelt kommando (`nixos capture screenshot --help`).

### Åbning af menuen fra terminalen

NixOS-menuen kan også scriptes, hvilket er praktisk til dine egne genvejstaster. `nixos menu` åbner den ved roden, og du kan springe direkte til ethvert punkt i træet ved at navngive det: `nixos menu summon appearance.theme` går direkte til temavælgeren, `nixos menu toggle system` åbner systemmenuen og lukker den igen, hvis den allerede er fremme, og `nixos menu close` gemmer den væk.
