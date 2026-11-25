# Capture and Sharing

Read this before taking screenshots or screen recordings, extracting text from
the screen, or sharing files with other machines.

## Screenshots

```bash
nixos screenshot                            # Interactive smart-region flow
nixos capture screenshot region             # Select a region
nixos capture screenshot windows            # Pick a window
nixos capture screenshot fullscreen save    # Full screen, straight to disk (no editor)
nixos capture screenshot scroll             # Capture and stitch a scrolling region
nixos screenshot --editor=overlay           # Opt into annotation before output
```

The first argument picks the Omasnap mode (`smart|region|windows|fullscreen|scroll`). By default, a capture saves to disk, copies to the clipboard, and shows a notification with the shot's thumbnail and Open and Edit buttons. Use its Edit button to annotate, or pass `--editor=overlay` or `--editor=window` to edit before output. A second argument of `copy` or `save` sends the screenshot straight to that destination. Saved screenshots land in `~/Pictures/Screenshots` by default (override with `OMASNAP_SCREENSHOT_DIR`; the legacy `NIXOS_SCREENSHOT_DIR` is also honored by the NixOS command). Set `[output] autosave = false` in `~/.config/omasnap/omasnap.conf` to disable automatic saving; captures are then only copied and shown in a 10-second preview.

## Screen Recording

```bash
nixos screenrecord --fullscreen             # Start recording the full screen
# ...exercise whatever you want on film...
nixos screenrecord --stop-recording         # Stop; prints the saved path
```

Optional flags: `--with-desktop-audio`, `--with-microphone-audio`,
`--with-webcam` (plus `--webcam-device=` and `--webcam-size=`), and
`--resolution=<size>`. Without `--fullscreen` a region picker opens first.
Recordings land in the configured Videos directory (override with
`NIXOS_SCREENRECORD_DIR`). Resize a live webcam overlay with
`nixos capture webcam resize <smaller|larger|reset|small|medium|large>`.

If recording fails to start, rerun with `NIXOS_SCREENRECORD_DEBUG=true` to
collect a log at `$XDG_RUNTIME_DIR/nixos-screenrecord.log` (or `${XDG_STATE_HOME:-$HOME/.local/state}/nixos/nixos-screenrecord.log` without a session runtime directory) worth attaching to a bug
report.

## Text Capture (OCR)

```bash
nixos capture text    # Select a region; extracted text goes to the clipboard
```

## Sharing Files

```bash
nixos share clipboard               # Share the clipboard via LocalSend
nixos share file <path...>          # Share files with nearby devices
nixos share folder <path>           # Share a folder

nixos tailscale send <machine> <file...>    # Taildrop to a tailnet machine
nixos tailscale receive [directory]         # Save incoming Taildrop files
```

Shrink large captures before sharing them:

```bash
nixos transcode <input> [format] [resolution]   # Re-encode pictures/videos for sharing
```
