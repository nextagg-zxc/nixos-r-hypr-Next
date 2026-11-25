# NixOS CLI

NixOS обычно управляется через горячие клавиши и меню NixOS (`Super + Space`). Но им также можно управлять через `nixos` CLI. Это особенно полезно, когда вы работаете с AI-агентом над кастомизацией или конфигурацией.

CLI имеет доступ ко всему внутреннему инструментарию, который используется как через меню, так и иным образом. Вы можете увидеть всё, что доступно, запустив `nixos` в терминале.

Выглядит это примерно так:

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

И по каждой группе можно углубиться:

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

Каждая команда тоже принимает `--help`, независимо от того, спрашиваете ли вы целую группу (`nixos capture --help`) или отдельную команду (`nixos capture screenshot --help`).

### Открытие меню из терминала

Меню NixOS также можно вызывать из скриптов, что удобно для ваших собственных привязок клавиш. `nixos menu` открывает его в корне, и вы можете перейти сразу к любому пункту дерева, назвав его: `nixos menu summon appearance.theme` сразу переходит к выбору темы, `nixos menu toggle system` открывает системное меню и снова закрывает его, если оно уже открыто, а `nixos menu close` убирает его.
