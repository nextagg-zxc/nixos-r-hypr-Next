# NixOS CLI

NixOS kwa kawaida hudhibitiwa kupitia njia za mkato za kibodi na menyu ya NixOS (`Super + Space`). Lakini pia unaweza kuudhibiti kupitia CLI ya `nixos`. Hii ni muhimu sana unapokuwa na agent ya AI inayofanya kazi pamoja nawe kwenye ubinafsishaji au usanidi.

CLI ina ufikiaji wa zana zote za ndani zinazotumika kupitia menyu na vinginevyo. Unaweza kuona kila kinachopatikana kwa kuendesha `nixos` kwenye terminal.

Inaonekana kitu kama hiki:

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

Na unaweza kuchimba zaidi katika kila kikundi:

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

Kila amri pia inakubali `--help`, iwe unauliza kikundi kizima (`nixos capture --help`) au amri moja (`nixos capture screenshot --help`).

### Kufungua menyu kutoka kwenye terminal

Menyu ya NixOS pia inaweza kuendeshwa kwa script, jambo ambalo ni muhimu kwa keybindings zako mwenyewe. `nixos menu` huifungua katika mzizi, na unaweza kuruka moja kwa moja hadi sehemu yoyote kwenye mti kwa kuitaja: `nixos menu summon appearance.theme` huenda moja kwa moja hadi kichaguzi cha mandhari, `nixos menu toggle system` hufungua menyu ya mfumo na kuifunga tena ikiwa tayari iko wazi, na `nixos menu close` huifunga.
