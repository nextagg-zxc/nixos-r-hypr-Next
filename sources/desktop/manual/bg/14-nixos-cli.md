# NixOS CLI

NixOS обикновено се управлява чрез клавишните комбинации и менюто на NixOS (`Super + Space`). Но можете да го управлявате и чрез `nixos` CLI. Това е особено полезно, когато AI агент работи с вас по персонализиране или конфигуриране.

CLI има достъп до всички вътрешни инструменти, които се използват както чрез менюто, така и по друг начин. Можете да видите всичко налично, като изпълните `nixos` в терминала.

Изглежда приблизително така:

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

И можете да навлезете по-дълбоко във всяка група:

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

Всяка команда приема и `--help`, независимо дали питате цяла група (`nixos capture --help`) или отделна команда (`nixos capture screenshot --help`).

### Отваряне на менюто от терминала

Менюто на NixOS също може да се скриптира, което е удобно за вашите собствени клавишни комбинации. `nixos menu` го отваря в основата, а можете да прескочите директно до всяка точка от дървото, като я назовете: `nixos menu summon appearance.theme` отива директно до избора на тема, `nixos menu toggle system` отваря системното меню и го затваря отново, ако вече е отворено, а `nixos menu close` го прибира.
