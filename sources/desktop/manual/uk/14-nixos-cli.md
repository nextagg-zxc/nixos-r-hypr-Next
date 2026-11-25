# NixOS CLI

NixOS зазвичай керують за допомогою гарячих клавіш і меню NixOS (`Super + Space`). Але керувати нею можна також через CLI `nixos`. Це особливо корисно, коли агент ШІ працює з вами над кастомізацією чи конфігурацією.

CLI має доступ до всіх внутрішніх інструментів, які використовуються як через меню, так і в інший спосіб. Ви можете побачити все доступне, запустивши `nixos` у терміналі.

Виглядає це приблизно так:

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

І ви можете заглибитися в кожну групу:

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

Кожна команда також приймає `--help`, незалежно від того, чи запитуєте ви цілу групу (`nixos capture --help`), чи окрему команду (`nixos capture screenshot --help`).

### Відкриття меню з термінала

Меню NixOS також можна скриптувати, що зручно для ваших власних прив'язок клавіш. `nixos menu` відкриває його в корені, і ви можете переходити прямо до будь-якої точки дерева, назвавши її: `nixos menu summon appearance.theme` веде прямо до вибору теми, `nixos menu toggle system` відкриває системне меню і знову закриває його, якщо воно вже відкрите, а `nixos menu close` прибирає його.
