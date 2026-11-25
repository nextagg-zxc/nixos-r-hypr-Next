# NixOS CLI

NixOS کو عام طور پر hotkeys اور NixOS menu (`Super + Space`) کے ذریعے کنٹرول کیا جاتا ہے۔ لیکن آپ اسے `nixos` CLI کے ذریعے بھی کنٹرول کر سکتے ہیں۔ یہ خاص طور پر اس وقت مددگار ہوتا ہے جب آپ کسی AI agent سے customization یا configuration پر اپنے ساتھ کام کروا رہے ہوں۔

CLI کو ان تمام internal tooling تک رسائی حاصل ہے جو menu کے ذریعے اور اس کے علاوہ بھی استعمال ہوتی ہیں۔ آپ terminal میں `nixos` چلا کر ہر دستیاب چیز دیکھ سکتے ہیں۔

یہ کچھ اس طرح نظر آتا ہے:

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

اور آپ ہر group میں مزید گہرائی تک جا سکتے ہیں:

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

ہر command `--help` بھی لیتا ہے، چاہے آپ پورے group سے پوچھیں (`nixos capture --help`) یا کسی ایک command سے (`nixos capture screenshot --help`)۔

### Terminal سے menu کھولنا

NixOS menu کو script بھی کیا جا سکتا ہے، جو آپ کی اپنی keybindings کے لیے کارآمد ہے۔ `nixos menu` اسے root پر کھولتا ہے، اور آپ اس کا نام دے کر tree میں سیدھا کسی بھی مقام پر جا سکتے ہیں: `nixos menu summon appearance.theme` سیدھا theme picker پر جاتا ہے، `nixos menu toggle system` system menu کھولتا ہے اور اگر وہ پہلے سے کھلا ہو تو اسے پھر سے بند کر دیتا ہے، اور `nixos menu close` اسے ہٹا دیتا ہے۔
