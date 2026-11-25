# NixOS CLI

NixOS biasanya dikendalikan melalui hotkey dan menu NixOS (`Super + Space`). Tapi kamu juga bisa mengendalikannya melalui CLI `nixos`. Ini sangat membantu saat kamu meminta agen AI bekerja bersamamu dalam kustomisasi atau konfigurasi.

CLI ini punya akses ke semua perkakas internal yang digunakan baik melalui menu maupun cara lain. Kamu bisa melihat semua yang tersedia dengan menjalankan `nixos` di terminal.

Tampilannya kurang lebih seperti ini:

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

Dan kamu bisa menyelami setiap grup lebih dalam:

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

Setiap perintah juga menerima `--help`, baik saat kamu menanyakan seluruh grup (`nixos capture --help`) maupun satu perintah saja (`nixos capture screenshot --help`).

### Membuka menu dari terminal

Menu NixOS juga bisa diskrip, yang berguna untuk keybinding kamu sendiri. `nixos menu` membukanya di root, dan kamu bisa langsung lompat ke titik mana pun di pohonnya dengan menyebut namanya: `nixos menu summon appearance.theme` langsung menuju pemilih tema, `nixos menu toggle system` membuka menu sistem dan menutupnya lagi jika sudah terbuka, dan `nixos menu close` menyingkirkannya.
