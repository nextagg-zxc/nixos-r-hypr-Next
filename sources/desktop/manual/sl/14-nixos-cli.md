# NixOS CLI

NixOS se običajno upravlja prek bližnjičnih tipk in menija NixOS (`Super + Space`). Lahko pa ga upravljate tudi prek CLI-ja `nixos`. To je še posebej uporabno, ko z vami pri prilagajanju ali konfiguriranju sodeluje agent umetne inteligence.

CLI ima dostop do vseh notranjih orodij, ki se uporabljajo tako prek menija kot tudi sicer. Vse, kar je na voljo, si lahko ogledate tako, da v terminalu zaženete `nixos`.

Videti je približno tako:

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

V vsako skupino pa se lahko poglobite še bolj:

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

Tudi vsak ukaz sprejema `--help`, ne glede na to, ali vprašate celotno skupino (`nixos capture --help`) ali posamezen ukaz (`nixos capture screenshot --help`).

### Odpiranje menija iz terminala

Meni NixOS je mogoče tudi skriptirati, kar je priročno za vaše lastne bližnjice na tipkovnici. `nixos menu` ga odpre v korenu, na katero koli točko v drevesu pa lahko skočite neposredno tako, da jo imenujete: `nixos menu summon appearance.theme` gre naravnost do izbirnika tem, `nixos menu toggle system` odpre sistemski meni in ga znova zapre, če je že odprt, `nixos menu close` pa ga pospravi.
