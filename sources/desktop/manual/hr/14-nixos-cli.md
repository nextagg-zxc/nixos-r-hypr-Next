# NixOS CLI

NixOSjem se obično upravlja putem tipkovničkih prečaca i NixOS izbornika (`Super + Space`). Ali njime možete upravljati i putem `nixos` CLI-ja. To je osobito korisno kada AI agent radi s vama na prilagodbi ili konfiguraciji.

CLI ima pristup svim internim alatima koji se koriste i putem izbornika i na druge načine. Sve što je dostupno možete vidjeti pokretanjem naredbe `nixos` u terminalu.

Izgleda otprilike ovako:

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

A možete i dublje zaroniti u svaku skupinu:

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

Svaka naredba također prihvaća `--help`, bilo da pitate cijelu skupinu (`nixos capture --help`) ili jednu naredbu (`nixos capture screenshot --help`).

### Otvaranje izbornika iz terminala

NixOS izbornik također se može skriptirati, što je zgodno za vlastite tipkovničke prečace. `nixos menu` otvara ga na korijenu, a možete skočiti izravno na bilo koju točku u stablu navodeći je: `nixos menu summon appearance.theme` vodi ravno na birač tema, `nixos menu toggle system` otvara izbornik sustava i ponovno ga zatvara ako je već otvoren, a `nixos menu close` ga uklanja.
