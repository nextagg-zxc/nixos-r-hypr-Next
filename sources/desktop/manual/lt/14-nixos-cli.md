# NixOS CLI

NixOS paprastai valdoma sparčiaisiais klavišais ir NixOS meniu (`Super + Space`). Tačiau ją taip pat galima valdyti per `nixos` CLI. Tai ypač naudinga, kai kartu su jumis pritaikymo ar konfigūravimo darbus atlieka AI agentas.

CLI turi prieigą prie visų vidinių įrankių, kurie naudojami tiek per meniu, tiek kitais būdais. Viską, kas prieinama, galite pamatyti terminale paleidę `nixos`.

Tai atrodo maždaug taip:

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

Ir galite gilintis į kiekvieną grupę:

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

Kiekviena komanda taip pat priima `--help`, nesvarbu, ar klausiate visos grupės (`nixos capture --help`), ar vienos komandos (`nixos capture screenshot --help`).

### Meniu atidarymas iš terminalo

NixOS meniu taip pat galima valdyti scenarijais, o tai patogu jūsų pačių klavišų susiejimams. `nixos menu` atidaro jį nuo šaknies, o jūs galite pereiti tiesiai į bet kurią medžio vietą ją įvardydami: `nixos menu summon appearance.theme` nukelia tiesiai į temų pasirinkimą, `nixos menu toggle system` atidaro sistemos meniu ir vėl jį uždaro, jei jis jau atidarytas, o `nixos menu close` jį paslepia.
