# NixOS CLI

NixOS は通常、ホットキーと NixOS メニュー（`Super + Space`）で操作します。しかし、`nixos` CLI からも操作できます。これは、AI エージェントにカスタマイズや設定を手伝ってもらうときに特に便利です。

CLI からは、メニュー経由などで使われている内部ツールのすべてにアクセスできます。利用可能なものはすべて、ターミナルで `nixos` を実行すれば確認できます。

だいたいこんな感じです：

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

さらに、各グループについても詳しく見られます：

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

すべてのコマンドでも `--help` が使えます。グループ全体（`nixos capture --help`）でも、個別のコマンド（`nixos capture screenshot --help`）でも同様です。

### ターミナルからメニューを開く

NixOS メニューはスクリプトからも操作でき、独自のキーバインドを作るときに便利です。`nixos menu` でルートから開きます。名前を指定すれば、ツリー内の任意の場所へ直接移動できます：`nixos menu summon appearance.theme` はテーマピッカーへ直行し、`nixos menu toggle system` はシステムメニューを開き、すでに開いている場合は閉じます。`nixos menu close` で閉じます。
