# NixOS CLI

NixOS er venjulega stjórnað með flýtilyklunum og NixOS-valmyndinni (`Super + Space`). En þú getur líka stjórnað því gegnum `nixos` CLI. Þetta er sérstaklega gagnlegt þegar þú ert að hafa AI agent að vinna með þér að sérstillingum eða uppsetningu.

CLI hefur aðgang að öllum innri verkfærunum sem eru notuð bæði gegnum valmyndina og annars staðar. Þú getur séð allt sem er í boði með því að keyra `nixos` í terminal.

Það lítur einhvern veginn svona út:

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

Og þú getur kafað dýpra í hvern hóp:

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

Sérhver skipun tekur líka `--help`, hvort sem þú spyrð heilan hóp (`nixos capture --help`) eða eina skipun (`nixos capture screenshot --help`).

### Að opna valmyndina úr terminal

Það er líka hægt að stýra NixOS-valmyndinni með forskriftum, sem er þægilegt fyrir þína eigin flýtilykla. `nixos menu` opnar hana við rótina og þú getur hoppað beint að hvaða stað sem er í trénu með því að nefna hann: `nixos menu summon appearance.theme` fer beint í þemavalið, `nixos menu toggle system` opnar kerfisvalmyndina og lokar henni aftur ef hún er þegar opin og `nixos menu close` leggur hana í burtu.
