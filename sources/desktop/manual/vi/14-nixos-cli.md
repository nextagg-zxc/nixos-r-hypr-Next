# NixOS CLI

NixOS thường được điều khiển qua các phím tắt và menu NixOS (`Super + Space`). Nhưng bạn cũng có thể điều khiển nó qua CLI `nixos`. Điều này đặc biệt hữu ích khi bạn đang để một AI agent làm việc cùng bạn về tùy chỉnh hoặc cấu hình.

CLI có quyền truy cập vào toàn bộ công cụ nội bộ được dùng cả qua menu lẫn theo các cách khác. Bạn có thể thấy mọi thứ có sẵn bằng cách chạy `nixos` trong terminal.

Nó trông đại khái như thế này:

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

Và bạn có thể đi sâu hơn vào từng nhóm:

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

Mọi lệnh cũng đều nhận `--help`, dù bạn hỏi cả một nhóm (`nixos capture --help`) hay một lệnh đơn lẻ (`nixos capture screenshot --help`).

### Mở menu từ terminal

Menu NixOS cũng có thể được điều khiển bằng script, điều này rất tiện cho các keybinding của riêng bạn. `nixos menu` mở nó ở cấp gốc, và bạn có thể nhảy thẳng đến bất kỳ điểm nào trong cây bằng cách gọi tên nó: `nixos menu summon appearance.theme` đi thẳng đến trình chọn theme, `nixos menu toggle system` mở menu hệ thống và đóng lại nếu nó đang mở, và `nixos menu close` đóng nó đi.
