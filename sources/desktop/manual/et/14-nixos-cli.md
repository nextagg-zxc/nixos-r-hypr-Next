# NixOS CLI

NixOSt juhitakse tavaliselt kiirklahvide ja NixOS menüü (`Super + Space`) kaudu. Aga seda saab juhtida ka `nixos` CLI kaudu. See on eriti abiks siis, kui lased mõnel AI agendil endaga koos kohandusi või seadistusi teha.

CLI-l on juurdepääs kõigile sisemistele tööriistadele, mida kasutatakse nii menüü kaudu kui ka muul viisil. Kõike saadaolevat näed, kui käivitad terminalis käsu `nixos`.

See näeb välja umbes selline:

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

Ja iga rühma puhul saad minna sügavamale:

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

Iga käsk võtab ka lippu `--help`, olenemata sellest, kas küsid tervet rühma (`nixos capture --help`) või üht käsku (`nixos capture screenshot --help`).

### Menüü avamine terminalist

NixOS menüü on samuti skriptitav, mis on käepärane oma kiirklahvide jaoks. `nixos menu` avab selle juurtasemel ja sa saad hüpata otse puu suvalisse kohta, kui selle nimega nimetad: `nixos menu summon appearance.theme` viib otse teemavalijasse, `nixos menu toggle system` avab süsteemimenüü ja sulgeb selle uuesti, kui see on juba üleval, ning `nixos menu close` paneb selle ära.
