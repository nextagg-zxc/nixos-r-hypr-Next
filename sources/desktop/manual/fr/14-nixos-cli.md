# NixOS CLI

NixOS se contrôle habituellement via les raccourcis clavier et le menu NixOS (`Super + Space`). Mais vous pouvez aussi le contrôler via la CLI `nixos`. C'est particulièrement utile lorsque vous faites travailler un agent IA avec vous sur la personnalisation ou la configuration.

La CLI a accès à tous les outils internes utilisés à la fois via le menu et autrement. Vous pouvez voir tout ce qui est disponible en exécutant `nixos` dans le terminal.

Cela ressemble à quelque chose comme ceci :

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

Et vous pouvez explorer chaque groupe plus en détail :

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

Chaque commande accepte aussi `--help`, que vous interrogiez un groupe entier (`nixos capture --help`) ou une seule commande (`nixos capture screenshot --help`).

### Ouvrir le menu depuis le terminal

Le menu NixOS est également scriptable, ce qui est pratique pour vos propres raccourcis clavier. `nixos menu` l'ouvre à la racine, et vous pouvez sauter directement à n'importe quel point de l'arborescence en le nommant : `nixos menu summon appearance.theme` va directement au sélecteur de thème, `nixos menu toggle system` ouvre le menu système et le referme s'il est déjà affiché, et `nixos menu close` le masque.
