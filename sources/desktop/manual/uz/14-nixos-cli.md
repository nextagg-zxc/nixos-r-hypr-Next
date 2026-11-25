# NixOS CLI

NixOS odatda tezkor tugmalar va NixOS menyusi (`Super + Space`) orqali boshqariladi. Lekin uni `nixos` CLI orqali ham boshqarishingiz mumkin. Bu, ayniqsa, moslashtirish yoki konfiguratsiya ustida siz bilan birga AI agent ishlayotganda juda qo‘l keladi.

CLI menyu orqali ham, boshqa yo‘llar bilan ham ishlatiladigan barcha ichki vositalarga kirish imkoniga ega. Mavjud barcha narsani terminalda `nixos` ni ishga tushirib ko‘rishingiz mumkin.

Bu taxminan shunday ko‘rinadi:

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

Va har bir guruhga yanada chuqurroq kirishingiz mumkin:

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

Har bir buyruq `--help` ni ham qabul qiladi, xoh butun guruhni so‘rasangiz (`nixos capture --help`), xoh bitta buyruqni so‘rasangiz (`nixos capture screenshot --help`).

### Menyuni terminaldan ochish

NixOS menyusini skript orqali ham boshqarish mumkin, bu o‘z tugmalar birikmalaringiz uchun qulay. `nixos menu` uni ildizidan ochadi va uni nomlash orqali daraxtning istalgan nuqtasiga to‘g‘ridan-to‘g‘ri o‘tishingiz mumkin: `nixos menu summon appearance.theme` to‘g‘ridan-to‘g‘ri mavzu tanlagichga o‘tadi, `nixos menu toggle system` tizim menyusini ochadi va agar u allaqachon ochiq bo‘lsa, uni yana yopadi, `nixos menu close` esa uni yopib qo‘yadi.
