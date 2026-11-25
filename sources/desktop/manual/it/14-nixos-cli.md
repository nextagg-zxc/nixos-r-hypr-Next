# NixOS CLI

NixOS viene di solito controllato tramite i tasti di scelta rapida e il menu di NixOS (`Super + Space`). Ma puoi controllarlo anche tramite la CLI `nixos`. Questo è particolarmente utile quando fai lavorare un agente AI insieme a te sulla personalizzazione o sulla configurazione.

La CLI ha accesso a tutta la strumentazione interna usata sia tramite il menu sia in altro modo. Puoi vedere tutto ciò che è disponibile eseguendo `nixos` nel terminale.

Ha un aspetto simile a questo:

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

E puoi approfondire ogni singolo gruppo:

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

Ogni comando accetta anche `--help`, sia che tu lo chieda a un intero gruppo (`nixos capture --help`) sia a un singolo comando (`nixos capture screenshot --help`).

### Aprire il menu dal terminale

Il menu di NixOS è anche scriptabile, il che è comodo per le tue associazioni di tasti personalizzate. `nixos menu` lo apre alla radice, e puoi saltare direttamente a qualsiasi punto dell'albero nominandolo: `nixos menu summon appearance.theme` va dritto al selettore del tema, `nixos menu toggle system` apre il menu di sistema e lo richiude se è già aperto, e `nixos menu close` lo mette via.
