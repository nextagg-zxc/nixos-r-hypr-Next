# NixOS CLI

Normalment, NixOS es controla amb les tecles d'accés ràpid i el menú d'NixOS (`Super + Space`). Però també el pots controlar amb la CLI `nixos`. Això és especialment útil quan tens un agent d'IA treballant amb tu en la personalització o la configuració.

La CLI té accés a totes les eines internes que s'utilitzen tant des del menú com d'altres maneres. Pots veure tot el que hi ha disponible executant `nixos` al terminal.

Té un aspecte semblant a aquest:

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

I pots aprofundir en cada grup:

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

Cada comanda també accepta `--help`, tant si preguntes per un grup sencer (`nixos capture --help`) com per una sola comanda (`nixos capture screenshot --help`).

### Obrir el menú des del terminal

El menú d'NixOS també es pot controlar amb scripts, cosa que va molt bé per a les teves pròpies assignacions de tecles. `nixos menu` l'obre a l'arrel, i pots anar directament a qualsevol punt de l'arbre anomenant-lo: `nixos menu summon appearance.theme` va directe al selector de temes, `nixos menu toggle system` obre el menú del sistema i el torna a tancar si ja és obert, i `nixos menu close` el tanca.
