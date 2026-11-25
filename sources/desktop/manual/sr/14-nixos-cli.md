# NixOS CLI

NixOS се обично контролише преко пречица на тастатури и NixOS менија (`Super + Space`). Али њиме можете да управљате и преко `nixos` CLI-ја. Ово је нарочито корисно када са вама на прилагођавању или конфигурисању ради AI агент.

CLI има приступ свим интерним алатима који се користе и преко менија и иначе. Све што је доступно можете да видите покретањем команде `nixos` у терминалу.

Изгледа отприлике овако:

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

И можете да зароните дубље у сваку групу:

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

Свака команда прихвата и `--help`, било да питате целу групу (`nixos capture --help`) или једну команду (`nixos capture screenshot --help`).

### Отварање менија из терминала

NixOS мени такође може да се контролише из скрипти, што је згодно за ваше сопствене пречице на тастатури. `nixos menu` га отвара у корену, а можете да скочите право на било коју тачку у стаблу тако што ћете је навести по имену: `nixos menu summon appearance.theme` иде право на бирач тема, `nixos menu toggle system` отвара системски мени и поново га затвара ако је већ отворен, а `nixos menu close` га склања.
