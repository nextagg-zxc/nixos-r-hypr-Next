# NixOS CLI

NixOS zwykle obsługuje się za pomocą skrótów klawiszowych i menu NixOS (`Super + Space`). Można nią jednak sterować także przez CLI `nixos`. Jest to szczególnie pomocne, gdy agent AI współpracuje z Tobą nad dostosowywaniem lub konfiguracją.

CLI ma dostęp do wszystkich wewnętrznych narzędzi używanych zarówno przez menu, jak i w inny sposób. Wszystko, co jest dostępne, zobaczysz po uruchomieniu `nixos` w terminalu.

Wygląda to mniej więcej tak:

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

Możesz też zajrzeć głębiej do każdej grupy:

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

Każde polecenie przyjmuje też `--help`, niezależnie od tego, czy zapytasz o całą grupę (`nixos capture --help`), czy o pojedyncze polecenie (`nixos capture screenshot --help`).

### Otwieranie menu z terminala

Menu NixOS można też obsługiwać skryptami, co przydaje się przy własnych skrótach klawiszowych. `nixos menu` otwiera je na poziomie głównym, a podając nazwę, możesz przejść od razu do dowolnego miejsca w drzewie: `nixos menu summon appearance.theme` prowadzi prosto do wyboru motywu, `nixos menu toggle system` otwiera menu systemowe i zamyka je ponownie, jeśli jest już otwarte, a `nixos menu close` je chowa.
