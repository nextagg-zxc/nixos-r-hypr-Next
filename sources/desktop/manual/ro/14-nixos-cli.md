# NixOS CLI

NixOS este controlat de obicei prin tastele rapide și prin meniul NixOS (`Super + Space`). Dar îl poți controla și prin CLI-ul `nixos`. Acest lucru este deosebit de util atunci când un agent AI lucrează cu tine la personalizare sau configurare.

CLI-ul are acces la toate instrumentele interne folosite atât prin meniu, cât și în alte moduri. Poți vedea tot ce este disponibil rulând `nixos` în terminal.

Arată cam așa:

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

Și poți aprofunda fiecare grup:

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

Fiecare comandă acceptă și `--help`, fie că întrebi un întreg grup (`nixos capture --help`), fie o singură comandă (`nixos capture screenshot --help`).

### Deschiderea meniului din terminal

Meniul NixOS poate fi folosit și în scripturi, ceea ce este util pentru propriile tale combinații de taste. `nixos menu` îl deschide la rădăcină, iar tu poți sări direct la orice punct din arbore numindu-l: `nixos menu summon appearance.theme` te duce direct la selectorul de teme, `nixos menu toggle system` deschide meniul de sistem și îl închide din nou dacă este deja deschis, iar `nixos menu close` îl ascunde.
