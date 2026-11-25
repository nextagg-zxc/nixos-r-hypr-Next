# NixOS CLI

NixOSä käytetään yleensä pikanäppäimillä ja NixOS-valikolla (`Super + Space`). Mutta voit hallita sitä myös `nixos` CLI:n kautta. Tämä on erityisen hyödyllistä, kun työskentelet tekoälyagentin kanssa mukautusten tai määritysten parissa.

CLI:llä on pääsy kaikkiin sisäisiin työkaluihin, joita käytetään sekä valikon kautta että muuten. Näet kaiken saatavilla olevan ajamalla `nixos` terminaalissa.

Se näyttää suunnilleen tältä:

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

Ja jokaiseen ryhmään voi sukeltaa syvemmälle:

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

Jokainen komento hyväksyy myös `--help`-vivun, kysyitpä sitä koko ryhmältä (`nixos capture --help`) tai yksittäiseltä komennolta (`nixos capture screenshot --help`).

### Valikon avaaminen terminaalista

NixOS-valikko on myös skriptattavissa, mikä on kätevää omia näppäinsidoksiasi varten. `nixos menu` avaa sen juuresta, ja voit hypätä suoraan mihin tahansa kohtaan puussa nimeämällä sen: `nixos menu summon appearance.theme` menee suoraan teeman valitsimeen, `nixos menu toggle system` avaa järjestelmävalikon ja sulkee sen uudelleen, jos se on jo auki, ja `nixos menu close` sulkee sen.
