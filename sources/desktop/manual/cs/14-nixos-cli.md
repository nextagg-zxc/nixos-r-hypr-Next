# NixOS CLI

NixOS se obvykle ovládá pomocí klávesových zkratek a menu NixOS (`Super + Space`). Ovládat ho ale můžete i prostřednictvím CLI `nixos`. To se hodí zejména tehdy, když s vámi na úpravách nebo konfiguraci pracuje AI agent.

CLI má přístup ke všem interním nástrojům, které se používají jak přes menu, tak i jinak. Vše, co je k dispozici, uvidíte po spuštění `nixos` v terminálu.

Vypadá to nějak takto:

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

A u každé skupiny můžete jít ještě hlouběji:

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

Každý příkaz přijímá i `--help`, ať už se zeptáte celé skupiny (`nixos capture --help`), nebo jednoho příkazu (`nixos capture screenshot --help`).

### Otevření menu z terminálu

Menu NixOS lze ovládat i skriptem, což se hodí pro vaše vlastní klávesové zkratky. `nixos menu` ho otevře na kořenové úrovni a pojmenováním můžete skočit rovnou na libovolné místo ve stromu: `nixos menu summon appearance.theme` přejde přímo do výběru motivu, `nixos menu toggle system` otevře systémové menu a zase ho zavře, pokud už je otevřené, a `nixos menu close` ho schová.
