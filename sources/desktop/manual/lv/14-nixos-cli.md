# NixOS CLI

NixOS parasti kontrolē ar karstajiem taustiņiem un NixOS izvēlni (`Super + Space`). Bet to var kontrolēt arī ar `nixos` CLI. Tas ir īpaši noderīgi, kad kopā ar tevi pie pielāgošanas vai konfigurēšanas strādā AI aģents.

CLI ir piekļuve visiem iekšējiem rīkiem, kas tiek izmantoti gan caur izvēlni, gan citādi. Visu pieejamo vari apskatīt, terminālī palaižot `nixos`.

Tas izskatās apmēram šādi:

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

Un vari iedziļināties katrā grupā:

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

Katrai komandai ir arī `--help`, neatkarīgi no tā, vai jautā veselai grupai (`nixos capture --help`) vai vienai komandai (`nixos capture screenshot --help`).

### Izvēlnes atvēršana no termināļa

NixOS izvēlne ir arī skriptējama, kas noder tavām paša taustiņu kombinācijām. `nixos menu` to atver saknē, un vari pāriet tieši uz jebkuru vietu kokā, to nosaucot: `nixos menu summon appearance.theme` aizved tieši uz motīvu izvēli, `nixos menu toggle system` atver sistēmas izvēlni un aizver to atkal, ja tā jau ir atvērta, un `nixos menu close` to aizver.
