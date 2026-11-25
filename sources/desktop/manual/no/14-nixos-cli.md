# NixOS CLI

NixOS styres vanligvis gjennom hurtigtastene og NixOS-menyen (`Super + Space`). Men du kan også styre det gjennom `nixos` CLI. Dette er særlig nyttig når du har en AI-agent som jobber sammen med deg med tilpasning eller konfigurasjon.

CLI-en har tilgang til all intern verktøystøtte som brukes både via menyen og ellers. Du kan se alt som er tilgjengelig ved å kjøre `nixos` i terminalen.

Det ser omtrent slik ut:

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

Og du kan dykke dypere ned i hver gruppe:

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

Alle kommandoer tar også `--help`, enten du spør en hel gruppe (`nixos capture --help`) eller en enkeltkommando (`nixos capture screenshot --help`).

### Åpne menyen fra terminalen

NixOS-menyen kan også skriptes, noe som er hendig for dine egne tastebindinger. `nixos menu` åpner den på rotnivå, og du kan hoppe rett til ethvert punkt i treet ved å navngi det: `nixos menu summon appearance.theme` går rett til temavelgeren, `nixos menu toggle system` åpner systemmenyen og lukker den igjen hvis den allerede er oppe, og `nixos menu close` legger den bort.
