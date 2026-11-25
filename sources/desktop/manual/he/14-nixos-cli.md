# NixOS CLI

את NixOS שולטים בדרך כלל דרך מקשי הקיצור והתפריט של NixOS (`Super + Space`). אבל אפשר לשלוט בה גם דרך ה-CLI של `nixos`. זה מועיל במיוחד כשסוכן AI עובד איתך על התאמה אישית או על תצורה.

ל-CLI יש גישה לכל הכלים הפנימיים שמשמשים גם דרך התפריט וגם בדרכים אחרות. אפשר לראות את כל מה שזמין על ידי הרצת `nixos` בטרמינל.

זה נראה בערך ככה:

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

ואפשר לצלול עמוק יותר לכל קבוצה:

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

כל פקודה מקבלת גם `--help`, בין אם שואלים קבוצה שלמה (`nixos capture --help`) או פקודה בודדת (`nixos capture screenshot --help`).

### פתיחת התפריט מהטרמינל

גם בתפריט של NixOS אפשר לשלוט באמצעות סקריפטים, וזה שימושי עבור מקשי הקיצור שלך. `nixos menu` פותח אותו מהשורש, ואפשר לקפוץ ישר לכל נקודה בעץ על ידי ציון שמה: `nixos menu summon appearance.theme` הולך ישר לבוחר ערכות הנושא, `nixos menu toggle system` פותח את תפריט המערכת וסוגר אותו שוב אם הוא כבר פתוח, ו-`nixos menu close` מסתיר אותו.
