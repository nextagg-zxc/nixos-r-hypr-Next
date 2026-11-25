# NixOS CLI

NixOS معمولاً از طریق کلیدهای میانبر و منوی NixOS (`Super + Space`) کنترل می‌شود. اما می‌توانید آن را از طریق CLI `nixos` هم کنترل کنید. این به‌ویژه زمانی مفید است که یک عامل هوش مصنوعی را برای همکاری با خودتان در سفارشی‌سازی یا پیکربندی به کار می‌گیرید.

CLI به همه ابزارهای داخلی‌ای دسترسی دارد که هم از طریق منو و هم به روش‌های دیگر استفاده می‌شوند. با اجرای `nixos` در ترمینال می‌توانید همه چیزهای در دسترس را ببینید.

چیزی شبیه این است:

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

و می‌توانید در هر گروه عمیق‌تر هم بشوید:

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

هر فرمان `--help` را هم می‌پذیرد، چه از یک گروه کامل بپرسید (`nixos capture --help`) و چه از یک فرمان منفرد (`nixos capture screenshot --help`).

### باز کردن منو از ترمینال

منوی NixOS قابل اسکریپت‌نویسی هم هست، که برای میانبرهای صفحه‌کلید خودتان به کار می‌آید. `nixos menu` آن را از ریشه باز می‌کند، و می‌توانید با نام بردن از آن مستقیم به هر نقطه‌ای از درخت بروید: `nixos menu summon appearance.theme` مستقیم به انتخاب‌گر تم می‌رود، `nixos menu toggle system` منوی سیستم را باز می‌کند و اگر از قبل باز باشد دوباره آن را می‌بندد، و `nixos menu close` آن را کنار می‌گذارد.
