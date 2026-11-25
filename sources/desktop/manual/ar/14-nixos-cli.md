# NixOS CLI

عادةً ما يتم التحكّم في NixOS عبر مفاتيح الاختصار وقائمة NixOS ‏(`Super + Space`). لكن يمكنك أيضًا التحكّم فيه عبر واجهة سطر الأوامر `nixos` CLI. وهذا مفيد بشكل خاص عندما تجعل وكيل ذكاء اصطناعي يعمل معك على التخصيص أو الإعداد.

تتمتّع واجهة سطر الأوامر بإمكانية الوصول إلى جميع الأدوات الداخلية المستخدمة سواء عبر القائمة أو بغير ذلك. يمكنك رؤية كل ما هو متاح بتشغيل `nixos` في الطرفية.

يبدو الأمر على نحو شبيه بهذا:

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

ويمكنك التعمّق أكثر في كل مجموعة:

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

يقبل كل أمر أيضًا `--help`، سواء طلبت مجموعة كاملة (`nixos capture --help`) أو أمرًا واحدًا (`nixos capture screenshot --help`).

### فتح القائمة من الطرفية

قائمة NixOS قابلة للبرمجة النصية أيضًا، وهو أمر مفيد لاختصارات لوحة المفاتيح الخاصة بك. يفتح `nixos menu` القائمة من الجذر، ويمكنك الانتقال مباشرة إلى أي نقطة في الشجرة بتسميتها: ينقلك `nixos menu summon appearance.theme` مباشرة إلى منتقي السمات، ويفتح `nixos menu toggle system` قائمة النظام ويغلقها مجددًا إذا كانت مفتوحة بالفعل، ويغلق `nixos menu close` القائمة ويخفيها.
