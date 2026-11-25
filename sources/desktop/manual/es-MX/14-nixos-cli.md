# NixOS CLI

Normalmente, NixOS se controla mediante las teclas de acceso rápido y el menú de NixOS (`Super + Space`). Pero también puedes controlarlo mediante la CLI `nixos`. Esto es especialmente útil cuando tienes a un agente de IA trabajando contigo en la personalización o la configuración.

La CLI tiene acceso a todas las herramientas internas que se usan tanto desde el menú como por otros medios. Puedes ver todo lo que está disponible ejecutando `nixos` en la terminal.

Se ve más o menos así:

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

Y puedes profundizar en cada grupo:

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

Todo comando también admite `--help`, ya sea que consultes un grupo completo (`nixos capture --help`) o un solo comando (`nixos capture screenshot --help`).

### Abrir el menú desde la terminal

El menú de NixOS también se puede controlar mediante comandos, lo que viene bien para tus propios atajos de teclado. `nixos menu` lo abre en la raíz, y puedes saltar directamente a cualquier punto del árbol nombrándolo: `nixos menu summon appearance.theme` va directo al selector de temas, `nixos menu toggle system` abre el menú del sistema y lo vuelve a cerrar si ya está abierto, y `nixos menu close` lo oculta.
