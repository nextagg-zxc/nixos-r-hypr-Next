# NixOS CLI

Az NixOSt általában a gyorsbillentyűkkel és az NixOS menüvel (`Super + Space`) vezérled. De az `nixos` CLI-n keresztül is vezérelheted. Ez különösen hasznos, amikor egy AI-ügynök dolgozik veled a testreszabáson vagy a konfiguráláson.

A CLI hozzáfér minden belső eszközhöz, amelyet a menün keresztül és más módokon is használ a rendszer. Minden elérhető lehetőséget megnézhetsz, ha futtatod az `nixos` parancsot a terminálban.

Valahogy így néz ki:

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

És minden csoportban mélyebbre is áshatsz:

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

Minden parancs elfogadja a `--help` kapcsolót is, akár egy egész csoportról kérdezel (`nixos capture --help`), akár egyetlen parancsról (`nixos capture screenshot --help`).

### A menü megnyitása a terminálból

Az NixOS menü is szkriptelhető, ami jól jön a saját billentyűparancsaidhoz. Az `nixos menu` a gyökérnél nyitja meg, és a fa bármely pontjára közvetlenül odaugorhatsz, ha megnevezed: az `nixos menu summon appearance.theme` egyenesen a témaválasztóhoz visz, az `nixos menu toggle system` megnyitja a rendszermenüt, és újra bezárja, ha már nyitva van, az `nixos menu close` pedig eltünteti.
