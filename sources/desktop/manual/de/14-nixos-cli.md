# NixOS CLI

NixOS wird in der Regel über die Hotkeys und das NixOS-Menü (`Super + Space`) gesteuert. Du kannst es aber auch über die `nixos`-CLI steuern. Das ist besonders hilfreich, wenn ein KI-Agent mit dir an Anpassungen oder Konfiguration arbeitet.

Die CLI hat Zugriff auf alle internen Werkzeuge, die sowohl über das Menü als auch anderweitig verwendet werden. Du kannst alles Verfügbare sehen, indem du `nixos` im Terminal ausführst.

Das sieht ungefähr so aus:

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

Und du kannst bei jeder Gruppe tiefer einsteigen:

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

Jeder Befehl akzeptiert auch `--help`, egal ob du eine ganze Gruppe (`nixos capture --help`) oder einen einzelnen Befehl (`nixos capture screenshot --help`) abfragst.

### Das Menü vom Terminal aus öffnen

Das NixOS-Menü ist ebenfalls skriptbar, was für deine eigenen Tastenkombinationen praktisch ist. `nixos menu` öffnet es auf der obersten Ebene, und du kannst direkt zu jedem Punkt im Baum springen, indem du ihn benennst: `nixos menu summon appearance.theme` führt direkt zur Theme-Auswahl, `nixos menu toggle system` öffnet das Systemmenü und schließt es wieder, wenn es bereits geöffnet ist, und `nixos menu close` schließt es.
