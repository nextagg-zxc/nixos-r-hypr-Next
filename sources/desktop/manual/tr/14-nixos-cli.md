# NixOS CLI

NixOS genellikle kısayol tuşları ve NixOS menüsü (`Super + Space`) aracılığıyla kontrol edilir. Ancak onu `nixos` CLI aracılığıyla da kontrol edebilirsiniz. Bu, özellikle bir AI agent ile birlikte özelleştirme veya yapılandırma üzerinde çalışırken faydalıdır.

CLI, hem menü aracılığıyla hem de başka yollarla kullanılan tüm dahili araçlara erişebilir. Terminalde `nixos` çalıştırarak mevcut olan her şeyi görebilirsiniz.

Görünümü aşağı yukarı şöyledir:

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

Ve her grubun derinliklerine de inebilirsiniz:

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

Her komut `--help` de kabul eder; ister bütün bir grubu (`nixos capture --help`) ister tek bir komutu (`nixos capture screenshot --help`) sorgulayın.

### Terminalden menüyü açma

NixOS menüsü de scriptlenebilir; bu, kendi tuş atamalarınız için kullanışlıdır. `nixos menu` onu kök düzeyde açar ve adını belirterek ağacın herhangi bir noktasına doğrudan atlayabilirsiniz: `nixos menu summon appearance.theme` doğrudan tema seçiciye gider, `nixos menu toggle system` sistem menüsünü açar ve zaten açıksa tekrar kapatır, `nixos menu close` ise onu ortadan kaldırır.
