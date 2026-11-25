# NixOS CLI

O NixOS é normalmente controlado através das teclas de atalho e do menu NixOS (`Super + Space`). Mas também pode controlá-lo através da CLI `nixos`. Isto é particularmente útil quando tem um agente de IA a trabalhar consigo na personalização ou na configuração.

A CLI tem acesso a todas as ferramentas internas utilizadas tanto através do menu como de outras formas. Pode ver tudo o que está disponível executando `nixos` no terminal.

Tem um aspeto semelhante a este:

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

E pode aprofundar cada grupo:

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

Todos os comandos também aceitam `--help`, quer pergunte a um grupo inteiro (`nixos capture --help`) quer a um único comando (`nixos capture screenshot --help`).

### Abrir o menu a partir do terminal

O menu NixOS também pode ser controlado por script, o que é útil para os seus próprios atalhos de teclado. `nixos menu` abre-o na raiz, e pode saltar diretamente para qualquer ponto da árvore indicando o respetivo nome: `nixos menu summon appearance.theme` vai diretamente para o seletor de temas, `nixos menu toggle system` abre o menu do sistema e volta a fechá-lo se já estiver aberto, e `nixos menu close` fecha-o.
