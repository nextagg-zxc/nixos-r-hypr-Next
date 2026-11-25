# NixOS CLI

O NixOS geralmente é controlado pelas teclas de atalho e pelo menu do NixOS (`Super + Space`). Mas você também pode controlá-lo pela CLI `nixos`. Isso é particularmente útil quando você tem um agente de IA trabalhando com você na personalização ou na configuração.

A CLI tem acesso a todas as ferramentas internas usadas tanto pelo menu quanto de outras formas. Você pode ver tudo o que está disponível executando `nixos` no terminal.

Ela se parece com algo assim:

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

E você pode se aprofundar em cada grupo:

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

Todo comando também aceita `--help`, seja ao consultar um grupo inteiro (`nixos capture --help`) ou um único comando (`nixos capture screenshot --help`).

### Abrindo o menu pelo terminal

O menu do NixOS também pode ser controlado por script, o que é útil para os seus próprios atalhos de teclado. `nixos menu` o abre na raiz, e você pode ir direto para qualquer ponto da árvore ao nomeá-lo: `nixos menu summon appearance.theme` vai direto para o seletor de temas, `nixos menu toggle system` abre o menu do sistema e o fecha novamente se ele já estiver aberto, e `nixos menu close` o fecha.
