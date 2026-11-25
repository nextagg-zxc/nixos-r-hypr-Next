# NixOS CLI

โดยปกติแล้ว NixOS จะควบคุมผ่านปุ่มลัดและเมนู NixOS (`Super + Space`) แต่คุณก็ควบคุมมันผ่าน `nixos` CLI ได้เช่นกัน วิธีนี้มีประโยชน์เป็นพิเศษเมื่อคุณให้ AI agent มาช่วยปรับแต่งหรือตั้งค่าต่าง ๆ ไปพร้อมกับคุณ

CLI เข้าถึงเครื่องมือภายในทั้งหมดที่ใช้ทั้งผ่านเมนูและช่องทางอื่น ๆ ได้ คุณดูทุกอย่างที่มีให้ใช้ได้ด้วยการรัน `nixos` ในเทอร์มินัล

หน้าตาของมันจะเป็นประมาณนี้:

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

และคุณยังเจาะลึกลงไปได้ในทุกกลุ่ม:

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

ทุกคำสั่งยังใช้ `--help` ได้เช่นกัน ไม่ว่าคุณจะถามทั้งกลุ่ม (`nixos capture --help`) หรือถามคำสั่งเดียว (`nixos capture screenshot --help`)

### การเปิดเมนูจากเทอร์มินัล

เมนู NixOS ก็สั่งงานด้วยสคริปต์ได้เช่นกัน ซึ่งสะดวกมากสำหรับ keybindings ของคุณเอง `nixos menu` จะเปิดเมนูที่จุดเริ่มต้น และคุณก็ข้ามตรงไปยังจุดใดก็ได้ในโครงสร้างเมนูด้วยการระบุชื่อจุดนั้น: `nixos menu summon appearance.theme` จะพาคุณตรงไปยังตัวเลือกธีมทันที `nixos menu toggle system` จะเปิดเมนูระบบ และปิดมันอีกครั้งหากเปิดอยู่แล้ว และ `nixos menu close` จะปิดเมนูทิ้งไป
