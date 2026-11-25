-- ============================================================================
-- Hyprland: the whole configuration in one file.
--
-- Sections:
--   1. Module path and reload handling
--   2. Desktop defaults (window rules, bindings, look, toggles, ...)
--   3. Personal modules (monitors, input, bindings, look and feel, ...)
--   4. Main: what is loaded and in which order
--
-- Each module is a package.preload entry, so require() takes it from this
-- file. Separate on purpose (written by programs): hypr/gui-settings.lua
-- (Hypr Settings) and ~/.local/state/nixos (theme, toggles, layouts).
-- Display scale changes from the menu are written into section 3 (monitors).
-- ============================================================================

-- ============================================================================
-- 1. Module path and reload handling
-- ============================================================================
-- Hyprland bootstrap for NixOS's Lua module path.

local home = os.getenv("HOME")
local reload_prefixes = {
  "default.hypr",
  "hypr",
  "nixos.current.theme",
}

local function should_reload_module(module)
  for _, prefix in ipairs(reload_prefixes) do
    if module == prefix or module:sub(1, #prefix + 1) == prefix .. "." then
      return true
    end
  end

  return false
end

local modules_to_reload = {}
for module in pairs(package.loaded) do
  if should_reload_module(module) then
    table.insert(modules_to_reload, module)
  end
end

for _, module in ipairs(modules_to_reload) do
  package.loaded[module] = nil
end

-- Load generated state from ~/.local/state, user modules from ~/.config, and
-- NixOS defaults from $NIXOS_PATH.
package.path = home
  .. "/.local/state/?.lua;"
  .. home
  .. "/.config/?.lua;"
  .. (os.getenv("NIXOS_PATH") or "/usr/share/nixos")
  .. "/?.lua;"
  .. package.path

-- ============================================================================
-- 2. Desktop defaults
-- ============================================================================
-- ----------------------------------------------------------------------------
-- default.hypr.apps
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps"] = function(...)
-- App-specific tweaks.
local paths = require("default.hypr.paths")
local require_all = require("default.hypr.require_all")

require_all.files(paths.nixos_path .. "/default/hypr/apps", "default.hypr.apps")
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.1password
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.1password"] = function(...)
-- 1Password 8.12 renamed its app id from "1Password" to the reverse-DNS form,
-- so match both to keep older installs floating too.
o.window("^(1[pP]assword|com\\.onepassword\\.OnePassword)$", { no_screen_share = true, tag = "+floating-window" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.battlenet
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.battlenet"] = function(...)
-- Battle.net launches under Proton; all its windows share class steam_app_battlenet.

-- The actual launcher: float-centered.
o.window({ class = "^steam_app_battlenet$", title = "^Battle\\.net$" }, {
  float = true,
  center = true,
  size = { 1280, 800 },
})

-- Installer: drop decorations and backdrop blur/shadow so the Blizzard chrome
-- isn't framed by the WM.
o.window({ class = "^steam_app_battlenet$", title = "^Battle\\.net Setup$" }, {
  decorate = false,
  no_blur = true,
  no_shadow = true,
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.bitwarden
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.bitwarden"] = function(...)
o.window("^([bB]itwarden)$", { no_screen_share = true, tag = "+floating-window" })

-- The extension's popout asks for the width set in its preferences and a height of its own,
-- so float it without the shared 875x600. The class varies by browser, profile and popup path.
o.window(".*nngceckbapebfimnlniiiahkandclblb.*", {
  no_screen_share = true,
  float = true,
  center = true,
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.browser
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.browser"] = function(...)
-- Browser tags and styling.
o.window("((google-)?[cC]hrom(e|ium)|[bB]rave-browser|[mM]icrosoft-edge|Vivaldi-stable|helium)", { tag = "+chromium-based-browser" })
o.window("([fF]irefox|zen|librewolf)", { tag = "+firefox-based-browser" })
o.window({ tag = "chromium-based-browser" }, { tile = true })

-- Video apps: remove the chromium browser tag so they can float.
o.window("(^.+-youtube\\.com__.*$|^.+-app\\.zoom\\.us__wc_home.*$)", { tag = "-chromium-based-browser" })

-- Hide screen sharing notification windows.
o.window({ title = ".*is sharing.*" }, { workspace = "special silent" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.captive-portal
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.captive-portal"] = function(...)
-- Captive portal sign-in: a small floating window, like macOS's, that
-- nixos-network-captive-portal closes once the internet is reachable.
local captive_portal = "^chrome-ping\\.omacom\\.io__.*$"
o.window(captive_portal, { tag = "-chromium-based-browser" })
o.window(captive_portal, { float = true, center = true, size = { 900, 760 } })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.davinci-resolve
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.davinci-resolve"] = function(...)
-- DaVinci Resolve window focus handling.
o.window(".*[Rr]esolve.*", {
  float = true,
  stay_focused = true,
  -- Prevent modal dialog pointer warps when focus follows the mouse.
  no_follow_mouse = true,
})

o.window({ class = ".*[Rr]esolve.*", title = "^DaVinci Resolve( Studio)? - .+$" }, { fullscreen = true })
-- Resolve exposes the Voiceover panel under the generic "Dialog" title.
o.window({ class = ".*[Rr]esolve.*", title = "^(DaVinci Resolve( Studio)? - .+|Project Manager|Preferences|Find Directory|Dialog)$" }, { stay_focused = false })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.geforce
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.geforce"] = function(...)
o.window("GeForceNOW", { idle_inhibit = "fullscreen" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.hermes
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.hermes"] = function(...)
-- Hermes Desktop's frameless HUD manages its own geometry.
o.window({ class = "^Hermes$", title = "^Hermes HUD$" }, {
  float = true,
  border_size = 0,
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.inkscape
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.inkscape"] = function(...)
-- Inkscape draws its file choosers itself rather than through the portal, so the portal rule never sees them.
o.window({
  class = "^org\\.inkscape\\.Inkscape$",
  title = "^Select file to (import|open|save to|save a copy to)$",
}, { tag = "+floating-window" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.jetbrains
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.jetbrains"] = function(...)
-- Disable mouse focus.
o.window("^(jetbrains-.*)$", { no_follow_mouse = true })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.localsend
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.localsend"] = function(...)
-- Float LocalSend and fzf file picker.
local localsend = "(org\\.localsend\\.)?localsend(_app)?"
o.window("Share", { float = true, center = true })
o.window(localsend, { float = true, center = true, size = { 1100, 700 } })
o.transparent_window(localsend)
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.moonlight
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.moonlight"] = function(...)
o.window("com.moonlight_stream.Moonlight", { fullscreen = true, idle_inhibit = "fullscreen" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.nixos-shell
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.nixos-shell"] = function(...)
-- Window and layer rules for the NixOS Quickshell surfaces. The
-- shell-wide bar / menu / popouts are layer-shell.

-- Keep the bar instant: no layer-shell fade/slide animation.
hl.layer_rule({ match = { namespace = "nixos-bar" }, no_anim = true, animation = "none" })

-- Launcher, image selector, emojis, clipboard overlays, the OSD, reminders, the
-- Wi-Fi QR code and keyboard-driven panels should pop without compositor layer
-- animations. Overlays open as soon as their scale is ready, without a
-- compositor fade or slide. Panels keep their own QML opacity transition
-- for normal open/close, and skip it for panel handoff.
hl.layer_rule({ match = { namespace = "^(nixos-menu|nixos-menu-dim|nixos-polkit-dim|nixos-image-selector|nixos-emojis|nixos-clipboard|nixos-keyboard-panel|nixos-osd|nixos-reminders|nixos-network-qr|nixos-dock|nixos-dock-apps|nixos-dock-apps-dim)$" }, no_anim = true, animation = "none" })

-- A boot intro hands the desktop between OWE's video layer and the shell's
-- background layer. The media fades itself, so a compositor fade on either
-- layer only dips the screen toward the empty desktop during the handoff.
hl.layer_rule({ match = { namespace = "^(nixos-background|owe-background)$" }, no_anim = true, animation = "none" })

-- Dev gallery is the main shell workbench; open it maximized like
-- SUPER+ALT+F so component previews have the whole workspace.
o.window({ class = "^org.quickshell$", title = "^NixOS shell – dev gallery$" }, { maximize = true })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.pip
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.pip"] = function(...)
-- Picture-in-picture overlays.
o.window({ title = "(Picture.?in.?[Pp]icture)" }, { tag = "+pip" })
o.window({ tag = "pip" }, {
  float = true,
  pin = true,
  size = { 600, 338 },
  keep_aspect_ratio = true,
  border_size = 0,
  move = { "(monitor_w-window_w-40)", "(monitor_h*0.04)" },
})

-- Google Meet PiP uses the meeting title instead of "Picture-in-Picture".
o.window({ tag = "chromium-based-browser", title = "^Meet - .+" }, {
  float = true,
  pin = true,
  size = { 600, 338 },
  keep_aspect_ratio = true,
  border_size = 0,
  move = { "(monitor_w-window_w-40)", "(monitor_h-window_h-40)" },
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.retroarch
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.retroarch"] = function(...)
o.window("com.libretro.RetroArch", {
  fullscreen = true,
  idle_inhibit = "fullscreen",
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.screenshot-selection
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.screenshot-selection"] = function(...)
-- Remove the 1px border around the slurp region selection used by recordings, OCR, and QR capture.
hl.layer_rule({ match = { namespace = "selection" }, no_anim = true, animation = "none" })

-- Keep the Omasnap overlay immediate. It stays visible to screen shares: hiding it blacks out the whole
-- fullscreen overlay in output captures, which breaks Omasnap's scroll capture.
hl.layer_rule({ match = { namespace = "^omasnap$" }, no_anim = true, animation = "none" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.steam
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.steam"] = function(...)
o.window("steam", { float = true, idle_inhibit = "fullscreen" })
o.window({ class = "steam", title = "Steam" }, { center = true, size = { 1100, 700 } })
o.window({ class = "steam", title = "Friends List" }, { size = { 460, 800 } })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.system
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.system"] = function(...)
-- Floating windows.
o.window({ tag = "floating-window" }, { float = true })
o.window({ tag = "floating-window" }, { center = true })
o.window({ tag = "floating-window" }, { size = { 875, 600 } })

o.window(
  "(org.nixos.btop|org.nixos.terminal|org.nixos.bash|org.codeberg.dnkl.foot|org.gnome.NautilusPreviewer|org.gnome.Evince|NixOS|About|TUI.float|imv|mpv)",
  {
    tag = "+floating-window",
  }
)

-- The portal only ever shows dialogs — file pickers, screen shares, permission
-- prompts — so every one of its windows belongs in the floating treatment,
-- whatever the app that asked for it titled it.
o.window("xdg-desktop-portal-gtk", { tag = "+floating-window" })
o.window({
  class = "(sublime_text|DesktopEditors|org.gnome.Nautilus)",
  title = "^(Open.*Files?|Open [F|f]older.*|Save.*Files?|Save.*As|Save|All Files|.*wants to [open|save].*|[C|c]hoose.*)",
}, { tag = "+floating-window" })

-- The About fastfetch layout needs more columns than the standard float provides.
-- This size only covers the first launch: nixos-launch-about measures the
-- rendered content, remembers the size that hugs it, and applies that as its own
-- rule before every later launch.
o.window("org.nixos.about", { float = true })
o.window("org.nixos.about", { center = true })
o.window("org.nixos.about", { size = { 920, 480 } })

o.window("omacalc", { float = true })

-- Fullscreen screensaver.
o.window("org.nixos.screensaver", { fullscreen = true })
o.window("org.nixos.screensaver", { float = true })
o.window("org.nixos.screensaver", { animation = "slide" })
-- The launcher picks each screensaver's workspace. A terminal mapped again as it closes lands out of sight instead,
-- where its fullscreen rule cannot take fullscreen from a window.
o.window("org.nixos.screensaver", { workspace = "special:screensaver silent" })

-- Popped window rounding.
o.window({ tag = "pop" }, { rounding = 8 })

-- Prevent idle while open.
o.window({ tag = "noidle" }, { idle_inhibit = "always" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.telegram
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.telegram"] = function(...)
-- Prevent Telegram from stealing focus on new messages.
o.window("org.telegram.desktop", { focus_on_activate = false })
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.terminals
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.terminals"] = function(...)
-- Define terminal tag so themes and bindings can single terminals out. NixOS
-- launches TUIs and its own terminal windows under dedicated app-ids
-- (org.nixos.btop, org.nixos.terminal, TUI.float, ...), so match those too.
-- The class is matched in full, so foot's other app-id needs spelling out.
o.window(
  "(Alacritty|kitty|com.mitchellh.ghostty|foot|org\\.codeberg\\.dnkl\\.foot|wezterm|org\\.nixos\\..*|TUI\\..*)",
  { tag = "+terminal" }
)
end

-- ----------------------------------------------------------------------------
-- default.hypr.apps.webcam-overlay
-- ----------------------------------------------------------------------------
package.preload["default.hypr.apps.webcam-overlay"] = function(...)
-- The 8:9 portrait presets scale from monitor height so they occupy the same
-- share of anything from a 1080p monitor to a scaled 6K display.
o.window("^WebcamOverlay-small$", {
  size = { "(monitor_h*4/25)", "(monitor_h*9/50)" },
  move = { "(monitor_w-monitor_h*4/25-40)", "(monitor_h-monitor_h*9/50-40)" },
})
o.window("^WebcamOverlay-medium$", {
  size = { "(monitor_h*2/9)", "(monitor_h/4)" },
  move = { "(monitor_w-monitor_h*2/9-40)", "(monitor_h-monitor_h/4-40)" },
})
o.window("^WebcamOverlay-large$", {
  size = { "(monitor_h*3/10)", "(monitor_h*27/80)" },
  move = { "(monitor_w-monitor_h*3/10-40)", "(monitor_h-monitor_h*27/80-40)" },
})

-- The dedicated app id keeps this out of mpv's generic centered floating rules,
-- so the camera appears at its final corner position.
o.window({ class = "^WebcamOverlay-(small|medium|large)$", title = "^WebcamOverlay$" }, {
  float = true,
  pin = true,
  no_initial_focus = true,
  no_dim = true,
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.autostart
-- ----------------------------------------------------------------------------
package.preload["default.hypr.autostart"] = function(...)
require("default.hypr.startup-cursor")

hl.on("hyprland.start", function()
  -- Applications inherit the user's cursor; only the compositor starts blank.
  if nixos_startup_cursor_pending then
    hl.env("XCURSOR_PATH", nixos_startup_cursor.path)
    hl.env("XCURSOR_THEME", nixos_startup_cursor.xcursor)
  end

  -- Slow app launch fix -- set systemd and D-Bus activation vars before
  -- starting session services.
  hl.exec_cmd("dbus-update-activation-environment --systemd --all")

  hl.exec_cmd("nixos-launch-shell")
  hl.exec_cmd("nixos-provision-first-run")
  hl.exec_cmd("nixos-powerprofiles-init")
  hl.exec_cmd(o.launch("nixos-hyprland-monitor-watch"))
  hl.exec_cmd(o.launch("udiskie --automount --no-notify --no-tray"))

  -- Start the herdr server inside the graphical session so its panes inherit
  -- WAYLAND_DISPLAY. Otherwise the first SSH login from a remote herdr starts
  -- it with a tty environment, and agents in its panes can't read the clipboard.
  hl.exec_cmd(o.launch("herdr server"))

  -- Run post-boot hooks after startup config has loaded.
  hl.exec_cmd("sleep 2 && nixos-hook post-boot")
end)
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings"] = function(...)
local paths = require("default.hypr.paths")
local require_all = require("default.hypr.require_all")

require_all.files(paths.nixos_path .. "/default/hypr/bindings", "default.hypr.bindings")
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings.applications
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings.applications"] = function(...)
-- Essential application bindings.
o.bind("SUPER + RETURN", "Terminal", o.launch_terminal())
o.bind("SUPER + SHIFT + RETURN", "Browser", { nixos = "browser" })
o.bind("SUPER + SHIFT + F", "File manager", { nixos = "nautilus" })
o.bind("SUPER + ALT + SHIFT + F", "File manager (cwd)", { nixos = "nautilus-cwd" })
o.bind("SUPER + SHIFT + B", "Browser", { nixos = "browser" })
o.bind("SUPER + SHIFT + ALT + B", "Browser (private)", { nixos = "browser --private" })
o.bind("SUPER + SHIFT + N", "Editor", { nixos = "editor" })

if o.preinstalled_bindings_enabled() then
  -- Bindings for preinstalled NixOS applications, TUIs, and web apps.
  o.bind("SUPER + ALT + RETURN", "Tmux", { nixos = "terminal-tmux" })
  o.bind("SUPER + CTRL + RETURN", "Herdr", { nixos = "terminal-herdr" })
  o.bind("SUPER + SHIFT + Q", "Calculator", "omacalc")
  o.bind("XF86Calculator", "Calculator", "omacalc")
  o.bind("SUPER + SHIFT + M", "Music", { nixos = "spotify" })
  o.bind("SUPER + SHIFT + ALT + M", "Music TUI", { tui = "cliamp", focus = true })
  if o.cmd_present("lazydocker") then
    o.bind("SUPER + SHIFT + D", "Docker", { tui = "nixos-launch-docker-tui" })
  end
  o.bind("SUPER + SHIFT + G", "Signal", { nixos = "signal" })
  o.bind("SUPER + SHIFT + O", "Obsidian", { launch = "obsidian", focus = "^obsidian$" })
  o.bind("SUPER + SHIFT + W", "Omawrite", { launch = "omawrite" })
  o.bind("SUPER + SHIFT + SLASH", "Passwords", { nixos = "1password" })

  o.bind("SUPER + SHIFT + A", "ChatGPT", { webapp = "https://chatgpt.com" })
  o.bind("SUPER + SHIFT + ALT + A", "Grok", { webapp = "https://grok.com" })
  o.bind("SUPER + SHIFT + C", "Calendar", { webapp = "https://app.hey.com/calendar/weeks/" })
  o.bind("SUPER + SHIFT + E", "Email", { webapp = "https://app.hey.com" })
  o.bind("SUPER + SHIFT + ALT + E", "New email", { webapp = "https://app.hey.com/messages/new?display=standalone&new_window=true" })
  o.bind("SUPER + SHIFT + Y", "YouTube", { webapp = "https://youtube.com/" })
  o.bind("SUPER + SHIFT + ALT + G", "WhatsApp", { webapp = "https://web.whatsapp.com/", focus = true })
  o.bind( "SUPER + SHIFT + CTRL + G", "Google Messages", { webapp = "https://messages.google.com/web/conversations", focus = true })
  o.bind("SUPER + SHIFT + P", "Google Photos", { webapp = "https://photos.google.com/", focus = true })
  o.bind("SUPER + SHIFT + S", "Google Maps", { webapp = "https://maps.google.com/", focus = true })
  o.bind("SUPER + SHIFT + X", "X", { webapp = "https://x.com/" })
  o.bind("SUPER + SHIFT + ALT + X", "X Post", { webapp = "https://x.com/compose/post" })
end
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings.clipboard
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings.clipboard"] = function(...)
-- Send with explicit mods to the focused surface by omitting the window target,
-- so universal clipboard shortcuts reach both normal windows and focused
-- layer-shell surfaces such as NixOS panels. A virtual keyboard (wtype) won't
-- do: the physically held SUPER merges into the injected chord at the seat.
-- The down/up split works around Hyprland send_shortcut sometimes leaving
-- synthetic key state stuck/repeating.
-- https://github.com/hyprwm/Hyprland/discussions/14099
local function send_shortcut_once(mods, key)
  return function()
    hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "down" }))

    hl.timer(function()
      hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "up" }))
    end, { timeout = 50, type = "oneshot" })
  end
end

-- Lean on the terminal tag from default/hypr/apps/terminals.lua so there's one
-- definition of what counts as a terminal. Dynamic tags carry a trailing "*".
local function active_window_is_terminal()
  local window = hl.get_active_window()
  if not window then
    return false
  end

  for _, tag in ipairs(window.tags or {}) do
    if tag:gsub("%*$", "") == "terminal" then
      return true
    end
  end

  return false
end

local function universal_clipboard_shortcut(default_mods, default_key, terminal_mods, terminal_key)
  return function()
    if active_window_is_terminal() then
      send_shortcut_once(terminal_mods, terminal_key)()
    else
      send_shortcut_once(default_mods, default_key)()
    end
  end
end

o.bind("SUPER + A", "Select all", send_shortcut_once("CTRL", "A"))
o.bind("SUPER + C", "Universal copy", universal_clipboard_shortcut("CTRL", "C", "CTRL SHIFT", "C"))
o.bind("SUPER + V", "Universal paste", universal_clipboard_shortcut("CTRL", "V", "CTRL SHIFT", "V"))
o.bind("SUPER + X", "Universal cut", send_shortcut_once("CTRL", "X"))
o.bind("SUPER + CTRL + V", "Clipboard manager", { panel = "nixos.clipboard" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings.dictation
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings.dictation"] = function(...)
-- Dictation keys are bound only once the chosen backend's own program is
-- installed (NixOS ships every adapter), so a selected backend that was
-- removed doesn't hold Right Alt (AltGr) or Alt + Space for nothing.
-- Personal bindings.lua dictation keys use the same check.
function o.dictation_installed()
  local pipe = io.popen("nixos-default-dictation 2>/dev/null", "r")
  local backend = pipe and pipe:read("*l")
  if pipe then
    pipe:close()
  end
  return backend ~= nil and backend:match("^[%w%-]+$") ~= nil and not o.cmd_missing(backend)
end

if o.dictation_installed() then
  o.bind("ALT + SPACE", "Toggle dictation", "nixos-dictation toggle")
  -- A modifier's mask changes between its press and release. Match the keysym
  -- independently of that mask; AltGr layouts use a different keysym.
  o.bind_hold("ALT + Alt_R", "Start dictation (push-to-talk)", "nixos-dictation start", "Stop dictation (push-to-talk)", "nixos-dictation stop", { ignore_mods = true })
end
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings.input-method
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings.input-method"] = function(...)
-- Same terminal tag test as clipboard.lua.
local function active_window_is_terminal()
  local window = hl.get_active_window()
  if not window then
    return false
  end

  for _, tag in ipairs(window.tags or {}) do
    if tag:gsub("%*$", "") == "terminal" then
      return true
    end
  end

  return false
end

-- Keep the desktop shortcut independent of Fcitx's custom switching keys.
-- Read the live Fcitx group so setup works without a compositor reload.
o.bind("SUPER + I", "Switch input language", "nixos-input-method cycle")
o.bind("SUPER + SHIFT + I", "Switch input language back", "nixos-input-method cycle back")

-- Pass the tmux/Herdr prefix through and return to direct input, so the next
-- key reaches the multiplexer instead of the engine's composition.
o.bind("CTRL + SPACE", "Direct input for the terminal prefix", function()
  if active_window_is_terminal() then
    -- Wait for the local controller reply before dispatching the next key.
    o.shell_succeeds("timeout 0.3 fcitx5-remote --check -c")
  end
end, { non_consuming = true })
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings.jis
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings.jis"] = function(...)
-- Defaults for Japanese (JIS) keyboards, which only apply when the installed
-- layout is jp. See default/hypr/keyboard.lua.

local keyboard = require("default.hypr.keyboard")

if not keyboard.jis() then
  return
end

-- Same down/up split as the universal clipboard shortcuts in clipboard.lua.
local function send_shortcut_once(mods, key)
  hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "down" }))

  hl.timer(function()
    hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "up" }))
  end, { timeout = 50, type = "oneshot" })
end

local function active_window_class()
  local window = hl.get_active_window()
  return ((window and window.class) or ""):lower()
end

-- On JIS, + is Shift + ;, so apps see Ctrl + Shift + semicolon and never zoom
-- in. Hand them Ctrl + keypad plus instead, which Chromium, Electron apps,
-- VS Code, and Firefox read as zoom in. Obsidian only listens for Ctrl + ^,
-- which JIS types without Shift.
local zoom_in_overrides = {
  obsidian = { "CTRL", "asciicircum" },
}

o.bind("CTRL + SHIFT + semicolon", "Zoom in (JIS + key)", function()
  local class = active_window_class()

  for pattern, chord in pairs(zoom_in_overrides) do
    if class:find(pattern, 1, true) then
      send_shortcut_once(chord[1], chord[2])
      return
    end
  end

  send_shortcut_once("CTRL", "KP_Add")
end)
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings.media
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings.media"] = function(...)
-- Volume, brightness, keyboard backlight, and touchpad controls.
o.bind("XF86AudioRaiseVolume", "Volume up", { audio = "raise" }, { locked = true, repeating = true })
o.bind("XF86AudioLowerVolume", "Volume down", { audio = "lower" }, { locked = true, repeating = true })
o.bind("XF86AudioMute", "Mute", { audio = "mute-toggle" }, { locked = true })
o.bind("XF86AudioMicMute", "Mute microphone", "nixos-audio-input-mute", { locked = true })
o.bind("XF86MonBrightnessUp", "Brightness up", { brightness = "raise" }, { locked = true, repeating = true })
o.bind("XF86MonBrightnessDown", "Brightness down", { brightness = "lower" }, { locked = true, repeating = true })
o.bind("SHIFT + XF86MonBrightnessUp", "Brightness maximum", "nixos-brightness-display 100%", { locked = true, repeating = true })
o.bind("SHIFT + XF86MonBrightnessDown", "Brightness minimum", "nixos-brightness-display 1%", { locked = true, repeating = true })
o.bind("XF86KbdBrightnessUp", "Keyboard brightness up", "nixos-brightness-keyboard up", { locked = true, repeating = true })
o.bind("XF86KbdBrightnessDown", "Keyboard brightness down", "nixos-brightness-keyboard down", { locked = true, repeating = true })
-- MacBooks have no keyboard-backlight keys. Ctrl and the display brightness
-- keys drive the keyboard backlight instead. The labels stay the short ones:
-- the keybindings menu elides a row past 78 characters.
o.bind("CTRL + XF86MonBrightnessDown", "Keyboard brightness down", "nixos-brightness-keyboard down", { locked = true, repeating = true })
o.bind("CTRL + XF86MonBrightnessUp", "Keyboard brightness up", "nixos-brightness-keyboard up", { locked = true, repeating = true })
o.bind("XF86KbdLightOnOff", "Keyboard backlight cycle", "nixos-brightness-keyboard cycle", { locked = true })
o.bind_toggle("XF86TouchpadToggle", "Toggle touchpad", "touchpad", { locked = true })
o.bind("XF86TouchpadOn", "Enable touchpad", "nixos-toggle-touchpad on", { locked = true })
o.bind("XF86TouchpadOff", "Disable touchpad", "nixos-toggle-touchpad off", { locked = true })

-- Precise volume and brightness controls.
o.bind("ALT + XF86AudioRaiseVolume", "Volume up precise", "nixos-audio-output-volume +1", { locked = true, repeating = true })
o.bind("ALT + XF86AudioLowerVolume", "Volume down precise", "nixos-audio-output-volume -1", { locked = true, repeating = true })
o.bind("ALT + XF86MonBrightnessUp", "Brightness up precise", "nixos-brightness-display +1%", { locked = true, repeating = true })
o.bind("ALT + XF86MonBrightnessDown", "Brightness down precise", "nixos-brightness-display 1%-", { locked = true, repeating = true })

-- Media controls.
o.bind("XF86AudioNext", "Next track", { ipc = "media.next" }, { locked = true })
o.bind("ALT + XF86AudioPlay", "Next track", { ipc = "media.next" }, { locked = true })
o.bind("XF86AudioPause", "Pause", { ipc = "media.playPause" }, { locked = true })
o.bind("XF86AudioPlay", "Play", { ipc = "media.playPause" }, { locked = true })
o.bind("XF86AudioPrev", "Previous track", { ipc = "media.previous" }, { locked = true })
o.bind("ALT + SHIFT + XF86AudioPlay", "Previous track", { ipc = "media.previous" }, { locked = true })
o.bind("XF86Eject", "Eject media", "eject", { locked = true })

o.bind("SHIFT + XF86AudioMute", "Switch audio output", "nixos-audio-output-switch", { locked = true })
o.bind("SHIFT + XF86AudioPause", "Switch media source", "nixos-audio-source-switch", { locked = true })
o.bind("SHIFT + XF86AudioPlay", "Switch media source", "nixos-audio-source-switch", { locked = true })
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings.tiling
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings.tiling"] = function(...)
o.bind("SUPER + W", "Close window", hl.dsp.window.close())
o.bind("SUPER + Q", "Close window", hl.dsp.window.close())
o.bind("CTRL + ALT + DELETE", "Close all windows", "nixos-hyprland-window-close-all")

o.bind("SUPER + J", "Toggle window split", hl.dsp.layout("togglesplit"))
o.bind("SUPER + P", "Pseudo window", hl.dsp.window.pseudo())
o.bind("SUPER + T", "Toggle window floating/tiling", hl.dsp.window.float({ action = "toggle" }))
o.bind("SUPER + F", "Full screen", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
o.bind("SUPER + CTRL + F", "Tiled full screen", "nixos-hyprland-window-tiled-fullscreen-toggle")
o.bind("SUPER + ALT + F", "Full width", hl.dsp.window.fullscreen({ mode = "maximized" }))
o.bind("SUPER + O", "Pop window out (float & pin)", "nixos-hyprland-window-pop")
o.bind("SUPER + ALT + Home", "Save window width", "nixos-hyprland-window-width save")
o.bind("SUPER + Home", "Restore window width", "nixos-hyprland-window-width restore")
o.bind("SUPER + L", "Cycle workspace layout", "nixos-hyprland-workspace-layout-toggle")
o.bind("SUPER + ALT + L", "Cycle workspace layout back", "nixos-hyprland-workspace-layout-toggle back")

o.bind("SUPER + LEFT", "Focus on left window", hl.dsp.focus({ direction = "l" }))
o.bind("SUPER + RIGHT", "Focus on right window", hl.dsp.focus({ direction = "r" }))
o.bind("SUPER + UP", "Focus on above window", hl.dsp.focus({ direction = "u" }))
o.bind("SUPER + DOWN", "Focus on below window", hl.dsp.focus({ direction = "d" }))

-- Each monitor has workspaces 1-10 of its own; see default/hypr/monitor-workspaces.lua.
for workspace = 1, 10 do
  local key = "code:" .. tostring(workspace + 9)
  o.bind("SUPER + " .. key, "Switch to workspace " .. workspace, o.workspaces.focus(workspace))
  o.bind("SUPER + SHIFT + " .. key, "Move window to workspace " .. workspace, o.workspaces.move_window(workspace))
  o.bind("SUPER + SHIFT + ALT + " .. key, "Move window silently to workspace " .. workspace, o.workspaces.move_window(workspace, false))
end

o.bind("SUPER + S", "Toggle scratchpad", hl.dsp.workspace.toggle_special("scratchpad"))
o.bind("SUPER + ALT + S", "Move window to scratchpad", hl.dsp.window.move({ workspace = "special:scratchpad", follow = false }))
o.bind("SUPER + grave", "Toggle Quake console", hl.dsp.workspace.toggle_special("qconsole"))
o.bind("SUPER + M", "Minimize window to the dock", "nixos-hyprland-window-minimize")
o.bind("SUPER + SHIFT + grave", "Move window to Quake console", hl.dsp.window.move({ workspace = "special:qconsole", follow = false }))

o.bind("SUPER + TAB", "Next workspace", hl.dsp.focus({ workspace = "m+1" }))
o.bind("SUPER + SHIFT + TAB", "Previous workspace", hl.dsp.focus({ workspace = "m-1" }))
o.bind("SUPER + CTRL + TAB", "Former workspace", hl.dsp.focus({ workspace = "previous_per_monitor" }))

o.bind("SUPER + SHIFT + ALT + LEFT", "Move workspace to left monitor", o.workspaces.move_to_monitor("l"))
o.bind("SUPER + SHIFT + ALT + RIGHT", "Move workspace to right monitor", o.workspaces.move_to_monitor("r"))
o.bind("SUPER + SHIFT + ALT + UP", "Move workspace to up monitor", o.workspaces.move_to_monitor("u"))
o.bind("SUPER + SHIFT + ALT + DOWN", "Move workspace to down monitor", o.workspaces.move_to_monitor("d"))

o.bind("SUPER + SHIFT + CTRL + LEFT", "Move window to left monitor", o.workspaces.move_window_to_monitor("l"))
o.bind("SUPER + SHIFT + CTRL + RIGHT", "Move window to right monitor", o.workspaces.move_window_to_monitor("r"))
o.bind("SUPER + SHIFT + CTRL + UP", "Move window to up monitor", o.workspaces.move_window_to_monitor("u"))
o.bind("SUPER + SHIFT + CTRL + DOWN", "Move window to down monitor", o.workspaces.move_window_to_monitor("d"))

o.bind("SUPER + SHIFT + LEFT", "Swap window to the left", hl.dsp.window.swap({ direction = "l" }))
o.bind("SUPER + SHIFT + RIGHT", "Swap window to the right", hl.dsp.window.swap({ direction = "r" }))
o.bind("SUPER + SHIFT + UP", "Swap window up", hl.dsp.window.swap({ direction = "u" }))
o.bind("SUPER + SHIFT + DOWN", "Swap window down", hl.dsp.window.swap({ direction = "d" }))

-- Going backwards lowers the window it leaves instead of raising the one it lands on: bring_to_top
-- moves the active window to the end of the same list cycle_next walks, so a raise here ping-pongs.
o.bind("ALT + SHIFT + TAB", "Reveal active window on top", hl.dsp.window.alter_zorder({ mode = "bottom" }))
o.bind("ALT + TAB", "Focus on next window", hl.dsp.window.cycle_next())
o.bind("ALT + SHIFT + TAB", "Focus on previous window", hl.dsp.window.cycle_next({ next = false }))
o.bind("ALT + TAB", "Reveal active window on top", hl.dsp.window.bring_to_top())

o.bind("CTRL + ALT + TAB", "Focus on next monitor", hl.dsp.focus({ monitor = "+1" }))
o.bind("CTRL + ALT + SHIFT + TAB", "Focus on previous monitor", hl.dsp.focus({ monitor = "-1" }))

o.bind("SUPER + code:20", "Expand window left", hl.dsp.window.resize({ x = -100, y = 0, relative = true }))
o.bind("SUPER + code:21", "Shrink window left", hl.dsp.window.resize({ x = 100, y = 0, relative = true }))
o.bind("SUPER + SHIFT + code:20", "Shrink window up", hl.dsp.window.resize({ x = 0, y = -100, relative = true }))
o.bind("SUPER + SHIFT + code:21", "Expand window down", hl.dsp.window.resize({ x = 0, y = 100, relative = true }))

o.bind("SUPER + ALT + code:20", "Expand window left a little", hl.dsp.window.resize({ x = -25, y = 0, relative = true }))
o.bind("SUPER + ALT + code:21", "Shrink window left a little", hl.dsp.window.resize({ x = 25, y = 0, relative = true }))
o.bind("SUPER + SHIFT + ALT + code:20", "Shrink window up a little", hl.dsp.window.resize({ x = 0, y = -25, relative = true }))
o.bind("SUPER + SHIFT + ALT + code:21", "Expand window down a little", hl.dsp.window.resize({ x = 0, y = 25, relative = true }))

o.bind("SUPER + CTRL + code:20", "Expand window left a lot", hl.dsp.window.resize({ x = -300, y = 0, relative = true }))
o.bind("SUPER + CTRL + code:21", "Shrink window left a lot", hl.dsp.window.resize({ x = 300, y = 0, relative = true }))
o.bind("SUPER + CTRL + SHIFT + code:20", "Shrink window up a lot", hl.dsp.window.resize({ x = 0, y = -300, relative = true }))
o.bind("SUPER + CTRL + SHIFT + code:21", "Expand window down a lot", hl.dsp.window.resize({ x = 0, y = 300, relative = true }))

o.bind("SUPER + mouse_down", "Scroll active workspace forward", hl.dsp.focus({ workspace = "m+1" }))
o.bind("SUPER + mouse_up", "Scroll active workspace backward", hl.dsp.focus({ workspace = "m-1" }))

o.bind("SUPER + mouse:272", "Move window", hl.dsp.window.drag(), { mouse = true })
o.bind("SUPER + mouse:273", "Resize window", hl.dsp.window.resize(), { mouse = true })

o.bind("SUPER + G", "Toggle window grouping", hl.dsp.group.toggle())
o.bind("SUPER + ALT + G", "Move active window out of group", hl.dsp.window.move({ out_of_group = true }))

o.bind("SUPER + ALT + LEFT", "Move window to group on left", hl.dsp.window.move({ into_group = "l" }))
o.bind("SUPER + ALT + RIGHT", "Move window to group on right", hl.dsp.window.move({ into_group = "r" }))
o.bind("SUPER + ALT + UP", "Move window to group on top", hl.dsp.window.move({ into_group = "u" }))
o.bind("SUPER + ALT + DOWN", "Move window to group on bottom", hl.dsp.window.move({ into_group = "d" }))

o.bind("SUPER + ALT + TAB", "Next window in group", hl.dsp.group.next())
o.bind("SUPER + ALT + SHIFT + TAB", "Previous window in group", hl.dsp.group.prev())

o.bind("SUPER + CTRL + LEFT", "Move grouped window focus left", hl.dsp.group.prev())
o.bind("SUPER + CTRL + RIGHT", "Move grouped window focus right", hl.dsp.group.next())

o.bind("SUPER + ALT + mouse_down", "Next window in group", hl.dsp.group.next())
o.bind("SUPER + ALT + mouse_up", "Previous window in group", hl.dsp.group.prev())

for index = 1, 5 do
  o.bind("SUPER + ALT + code:" .. tostring(index + 9), "Switch to group window " .. index, hl.dsp.group.active({ index = index }))
end

o.bind("SUPER + SLASH", "Monitor scaling up", "nixos-hyprland-monitor-scaling up")
o.bind("SUPER + ALT + SLASH", "Monitor scaling down", "nixos-hyprland-monitor-scaling down")
end

-- ----------------------------------------------------------------------------
-- default.hypr.bindings.utilities
-- ----------------------------------------------------------------------------
package.preload["default.hypr.bindings.utilities"] = function(...)
o.bind("SUPER + SPACE", "Menu", { menu = "root" })
o.bind("SUPER + ALT + SPACE", "Apps", "nixos-shell nixos.dock apps")
o.bind("SUPER + CTRL + E", "Emojis", { panel = "nixos.emojis" })
o.bind("SUPER + CTRL + C", "Capture menu", { menu = "capture" })
o.bind("SUPER + CTRL + O", "Toggle menu", { menu = "toggle" })
o.bind("SUPER + CTRL + H", "Hardware menu", { menu = "hardware" })
o.bind("SUPER + SHIFT + code:201", "Menu", { menu = "root" })
o.bind("SUPER + ESCAPE", "System menu", { menu = "system" })
o.bind("XF86PowerOff", "Power menu", { menu = "system" }, { locked = true })
o.bind("SUPER + K", "Keybindings", "nixos-menu-keybindings")
o.bind("SUPER + ALT + K", "Tmux keybindings", "nixos-menu-tmux-keybindings")
o.bind("SUPER + CTRL + K", "Herdr keybindings", "nixos-menu-herdr-keybindings")
o.bind_toggle("SUPER + SHIFT + SPACE", "Toggle top bar", "bar")
o.bind("SUPER + CTRL + SPACE", "Background switcher", { menu = "background" })
o.bind("SUPER + CTRL + W", "Background switcher", { menu = "background" })
o.bind("SUPER + SHIFT + CTRL + SPACE", "Theme menu", { menu = "theme" })
o.bind("SUPER + CTRL + T", "Theme menu", { menu = "theme" })
o.bind("SUPER + BACKSPACE", "Toggle transparency on a window", "nixos-hyprland-window-transparency-toggle")
o.bind("SUPER + SHIFT + BACKSPACE", "Toggle window gaps", "nixos-hyprland-window-gaps-toggle")
o.bind("SUPER + CTRL + BACKSPACE", "Toggle single-window square aspect", "nixos-hyprland-window-single-square-aspect-toggle")
o.bind_toggle("SUPER + CTRL + ALT + F", "Toggle full screen desktop", "fullscreen-desktop")

-- xkbcommon names the comma keysym "comma"; the upper-case "COMMA" does not match.
o.bind("SUPER + comma", "Dismiss, invoke, or focus last notification", { ipc = "notifications.act" })
o.bind("SUPER + SHIFT + comma", "Dismiss all notifications", { ipc = "notifications.dismissAll" })
o.bind("SUPER + CTRL + comma", "Control notifications with the keyboard", { ipc = "notifications.keyboard" })
o.bind("SUPER + ALT + comma", "Dismiss last notification", { ipc = "notifications.dismissOne" })
o.bind("SUPER + SHIFT + ALT + comma", "Open notification history", { ipc = "notifications.showHistory" })
o.bind_toggle("SUPER + CTRL + ALT + comma", "Toggle silencing notifications", "notification-silencing")

o.bind_toggle("SUPER + CTRL + I", "Toggle locking on idle", "idle")
o.bind("SUPER + CTRL + Delete", "Toggle laptop display", "nixos-hyprland-monitor-internal toggle")
o.bind("SUPER + CTRL + ALT + Delete", "Toggle laptop display mirroring", "nixos-hyprland-monitor-internal-mirror toggle")
o.bind("switch:on:Lid Switch", nil, "nixos-system-lid-close", { locked = true })
o.bind("switch:off:Lid Switch", nil, "nixos-hyprland-monitor-clamshell", { locked = true })
-- Apple Silicon reports its lid through the SMC, under its own switch name.
o.bind("switch:on:Apple SMC power/lid events", nil, "nixos-system-lid-close", { locked = true })
o.bind("switch:off:Apple SMC power/lid events", nil, "nixos-hyprland-monitor-clamshell", { locked = true })

o.bind("PRINT", "Screenshot", "nixos-capture-screenshot")
o.bind("SUPER + CTRL + ALT + C", "Screenshot", "nixos-capture-screenshot")
o.bind("ALT + PRINT", "Screenrecording", "nixos-capture-screenrecording --stop-recording || nixos-menu toggle trigger.capture.screenrecord")
o.bind("SUPER + ALT + code:34", "Make webcam overlay smaller", "nixos-capture-webcam-resize smaller")
o.bind("SUPER + ALT + code:35", "Make webcam overlay larger", "nixos-capture-webcam-resize larger")
o.bind("SUPER + PRINT", "Color picker", "pkill hyprpicker || hyprpicker -a")
o.bind("SUPER + CTRL + PRINT", "Extract text (OCR) from screenshot", "nixos-capture-text")

-- Keyboard control for the slurp region picker (see nixos-capture-region).
-- The binds are enabled exactly as long as a selection layer is on screen
-- (slurp opens one per monitor), so they cannot leak or get stuck.
-- They are disabled rather than unbound, since Hyprland's unbind() removes every
-- bind on the chord, the user's own included. Without descriptions, the
-- keybindings menu leaves them out.
local selection_layers = 0
local selection_keys = {
  ["RETURN"] = "--take-window",
  ["CTRL + RETURN"] = "--take-fullscreen",
  ["TAB"] = "--select-window next",
  ["CTRL + TAB"] = "--select-window prev",
  ["LEFT"] = "--select-window left",
  ["RIGHT"] = "--select-window right",
  ["UP"] = "--select-window up",
  ["DOWN"] = "--select-window down",
}
local selection_binds = {}

-- Any unbind of the chord expires the handle, and Hyprland 0.56 dereferences an
-- expired handle in every method but tostring().
local function selection_bind_alive(keybind)
  return keybind ~= nil and tostring(keybind) ~= "HL.Keybind(expired)"
end

hl.on("layer.opened", function(layer)
  if layer.namespace == "selection" then
    selection_layers = selection_layers + 1
    if selection_layers == 1 then
      for keys, mode in pairs(selection_keys) do
        if not selection_bind_alive(selection_binds[keys]) then
          selection_binds[keys] = hl.bind(keys, hl.dsp.exec_cmd("nixos-capture-region " .. mode))
        end
        selection_binds[keys]:set_enabled(true)
      end
    end
  end
end)

hl.on("layer.closed", function(layer)
  if layer.namespace == "selection" and selection_layers > 0 then
    selection_layers = selection_layers - 1
    if selection_layers == 0 then
      for _, keybind in pairs(selection_binds) do
        if selection_bind_alive(keybind) then
          keybind:set_enabled(false)
        end
      end
    end
  end
end)

o.bind("SUPER + CTRL + S", "Share", { menu = "share" })

o.bind("SUPER + CTRL + PERIOD", "Transcode", "nixos-transcode")

o.bind("SUPER + CTRL + R", "Set reminder", { menu = "reminder-set" })
o.bind("SUPER + CTRL + ALT + R", "Show reminders", "nixos-reminder show")
o.bind("SUPER + SHIFT + CTRL + R", "Clear reminders", "nixos-reminder clear")

o.bind("SUPER + CTRL + ALT + T", "Show time", "nixos-notification-time")
o.bind("SUPER + CTRL + ALT + B", "Show battery remaining", "nixos-notification-battery")
o.bind("SUPER + CTRL + ALT + W", "Toggle weather", "nixos-notification-weather")

o.bind("SUPER + SHIFT + CTRL + A", "Agent", "nixos-agent --pick")
o.bind("SUPER + CTRL + A", "Audio", { panel = "nixos.audio" })
o.bind("SUPER + CTRL + B", "Bluetooth", { panel = "nixos.bluetooth" })
o.bind("SUPER + CTRL + D", "Display", { panel = "nixos.monitor" })
o.bind("SUPER + CTRL + ALT + D", "Calendar", { panel = "nixos.clock" })
o.bind("SUPER + CTRL + ALT + E", "World clock", { panel = "nixos.elsewhen" })
o.bind("SUPER + CTRL + N", "Network", { panel = "nixos.network" })
o.bind("SUPER + CTRL + P", "Power", { panel = "nixos.power" })
o.bind("SUPER + SHIFT + T", "Activity", { tui = "btop" })

-- The letters above name a panel; the numbers count them. 1 is the leftmost
-- panel in the bar's right section, and a widget with no panel of its own (the
-- tray) is not counted, so the number matches the icon a user would point at.
-- A bar with fewer panels than this leaves the tail of the range doing nothing.
for panel = 1, 9 do
  o.bind(
    "SUPER + CTRL + code:" .. tostring(panel + 9),
    "Bar panel " .. panel,
    "nixos-shell -q shell togglePanelAt right " .. panel
  )
end

o.bind("SUPER + CTRL + Z", "Zoom in", function()
  local zoom = hl.get_config("cursor.zoom_factor") or 1
  hl.config({ cursor = { zoom_factor = zoom + 1 } })
end)

o.bind("SUPER + CTRL + ALT + Z", "Reset zoom", function()
  hl.config({ cursor = { zoom_factor = 1 } })
end)

o.bind("SUPER + CTRL + L", "Lock system", "nixos-system-lock")
end

-- ----------------------------------------------------------------------------
-- default.hypr.dictation-backend
-- ----------------------------------------------------------------------------
package.preload["default.hypr.dictation-backend"] = function(...)
-- Backends may supply their own desktop integration without editing the
-- user's Hyprland config. Recording bindings remain owned by NixOS.
local paths = require("default.hypr.paths")
local pipe = io.popen("nixos-default-dictation 2>/dev/null", "r")
if not pipe then
  return
end

local backend = pipe:read("*l")
pipe:close()

if not backend or not backend:match("^[%w%-]+$") or o.cmd_missing("nixos-dictation-" .. backend) then
  return
end

local integration = paths.config_home .. "/" .. backend .. "/shortcuts.lua"
local file = io.open(integration, "r")
if file then
  file:close()
  local ok, error = pcall(dofile, integration)
  if not ok then
    print("Could not load dictation backend " .. backend .. ": " .. tostring(error))
  end
end
end

-- ----------------------------------------------------------------------------
-- default.hypr.disabled-input-device
-- ----------------------------------------------------------------------------
package.preload["default.hypr.disabled-input-device"] = function(...)
-- Disable a Hyprland input device whose name was stored as data, not Lua.
-- Device names come from USB descriptors and must never be loaded as code.

local paths = require("default.hypr.paths")

return function(kind)
  -- Hardcoded to ~/.local/state to match nixos-toggle-input-device and the
  -- sibling bash toggle tools, which all write there regardless of
  -- XDG_STATE_HOME.
  local file = io.open(paths.home .. "/.local/state/nixos/toggles/hypr/" .. kind .. "-disabled-name", "r")
  if not file then
    return
  end

  local name = file:read("*l")
  file:close()

  if name and name ~= "" then
    hl.device({ name = name, enabled = false })
  end
end
end

-- ----------------------------------------------------------------------------
-- default.hypr.envs
-- ----------------------------------------------------------------------------
package.preload["default.hypr.envs"] = function(...)
local paths = require("default.hypr.paths")
local require_optional = require("default.hypr.require_optional")

-- GUM environment variables for styling purposes.
require_optional.module("nixos.current.theme.gum_env")

-- Cursor size.
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- Force all apps to use Wayland.
hl.env("GDK_BACKEND", "wayland,x11,*")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_QPA_PLATFORMTHEME", "gtk3")
hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "wayland")
hl.env("OZONE_PLATFORM", "wayland")
hl.env("XDG_SESSION_TYPE", "wayland")

-- Allow better support for screen sharing (Google Meet, Discord, etc).
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")

-- Use XCompose file.
hl.env("XCOMPOSEFILE", paths.home .. "/.XCompose")

-- hyprctl setenv doesn't reach keybind dispatcher env; use hl.env.
hl.env("NIXOS_PATH", paths.nixos_path)

local bin_dir = paths.nixos_path .. "/bin"
local kept = {}
for entry in (os.getenv("PATH") or "/usr/local/bin:/usr/bin"):gmatch("[^:]+") do
  if entry ~= bin_dir then table.insert(kept, entry) end
end
table.insert(kept, 1, bin_dir)
hl.env("PATH", table.concat(kept, ":"))

-- Hardware-specific environment.
require("default.hypr.nvidia")

hl.config({
  xwayland = {
    force_zero_scaling = true,
  },

  ecosystem = {
    no_update_news = true,
    no_donation_nag = true,
  },
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.glass
-- ----------------------------------------------------------------------------
package.preload["default.hypr.glass"] = function(...)
-- Frosted glass from the glassy Starship (#14726), shared by Glassy windows and
-- the Glassy bar: whatever is behind a see-through surface is blurred.
return function()
  hl.config({
    decoration = {
      blur = {
        enabled = true,
        size = 4,
        passes = 2,
        new_optimizations = true,
        xray = false,
        contrast = 1.0,
        brightness = 0.75,
        noise = 0.01,
        vibrancy = 0.35,
        vibrancy_darkness = 0.35,
        popups = true,
        special = true,
      },
    },
  })
end
end

-- ----------------------------------------------------------------------------
-- default.hypr.helpers
-- ----------------------------------------------------------------------------
package.preload["default.hypr.helpers"] = function(...)
-- Shared helpers for Hyprland Lua configuration.

local paths = require("default.hypr.paths")

o = o or {}

local function shell_quote(value)
  return "'" .. tostring(value):gsub("'", "'\\''") .. "'"
end

o.shell_quote = shell_quote

local function file_exists(path)
  local file = io.open(path, "r")
  if file then
    file:close()
    return true
  end

  return false
end

-- Hyprland reaps its own children, so os.execute() can't retrieve an exit status
-- from inside the compositor. Read a marker off stdout instead.
function o.shell_succeeds(command)
  -- Subshell, so the redirection covers every command rather than binding to
  -- the last one and letting an earlier one write its own OK into the pipe.
  local pipe = io.popen("( " .. command .. " ) >/dev/null 2>&1 && echo OK")
  if not pipe then
    return false
  end

  local output = pipe:read("*a") or ""
  pipe:close()

  return output:find("OK", 1, true) ~= nil
end

function o.cmd_present(command)
  if command:find("/", 1, true) then
    return file_exists(command)
  end

  local path = os.getenv("PATH") or "/usr/local/bin:/usr/bin"
  for directory in (path .. ":"):gmatch("([^:]*):") do
    if file_exists((directory ~= "" and directory or ".") .. "/" .. command) then
      return true
    end
  end

  return false
end

function o.cmd_missing(command)
  return not o.cmd_present(command)
end

-- The global shortcuts the shell registers, read from the same list it reads.
local shell_shortcuts = nil

local function shell_shortcut_registered(name)
  if not shell_shortcuts then
    shell_shortcuts = {}
    local file = io.open(paths.nixos_path .. "/default/nixos/shortcuts", "r")
    if file then
      for line in file:lines() do
        local kind, target = line:match("^(%a+)%s+(%S+)%s*$")
        if kind then
          shell_shortcuts[kind .. "." .. target] = true
        end
      end
      file:close()
    end
  end

  return shell_shortcuts[name] == true
end

-- Reach the shell through its global shortcut when it registers one, so the
-- keypress spawns nothing. Anything else runs the command as before.
local function shell_dispatcher(kind, target, command)
  local name = kind .. "." .. target
  if shell_shortcut_registered(name) then
    return hl.dsp.global("nixos:" .. name)
  end

  return command
end

local function command_from(value, description)
  if type(value) ~= "table" then
    return value
  end

  if value.nixos then
    return "nixos-launch-" .. value.nixos
  elseif value.menu then
    return shell_dispatcher("menu", value.menu, "nixos-menu toggle " .. shell_quote(value.menu))
  elseif value.panel then
    return shell_dispatcher("panel", value.panel, "nixos-shell shell toggle " .. shell_quote(value.panel))
  elseif value.audio then
    return shell_dispatcher("audio", value.audio, "nixos-audio-output-volume " .. shell_quote(value.audio))
  elseif value.brightness then
    local step = value.brightness == "raise" and "+5%" or "5%-"
    return shell_dispatcher("brightness", value.brightness, "nixos-brightness-display " .. step)
  elseif value.ipc then
    local target, method = value.ipc:match("^([^.]+)%.(.+)$")
    return shell_dispatcher("ipc", value.ipc, "nixos-shell " .. shell_quote(target) .. " " .. shell_quote(method))
  elseif value.focus and value.launch then
    return o.launch_sole(value.focus, value.launch)
  elseif value.launch then
    return o.launch(value.launch)
  elseif value.webapp then
    if value.focus then
      return o.launch_webapp_sole(description, value.webapp)
    else
      return o.launch_webapp(value.webapp)
    end
  elseif value.tui then
    if value.focus then
      return "nixos-launch-or-focus-tui " .. shell_quote(value.tui)
    else
      return "nixos-launch-tui " .. shell_quote(value.tui)
    end
  end

  return value
end

function o.preinstalled_bindings_enabled()
  if _G.nixos_preinstalled_bindings ~= nil then
    return _G.nixos_preinstalled_bindings == true
  end

  return not file_exists((os.getenv("HOME") or "") .. "/.local/state/nixos/preinstalls-removed")
end

function o.bind(keys, description, dispatcher, options)
  local opts = options or {}

  if description then
    opts.description = description
  end

  dispatcher = command_from(dispatcher, description)

  if type(dispatcher) == "string" then
    dispatcher = hl.dsp.exec_cmd(dispatcher)
  end

  hl.bind(keys, dispatcher, opts)
end

function o.rebind(keys, description, dispatcher, options)
  hl.unbind(keys)
  o.bind(keys, description, dispatcher, options)
end

function o.launch(command)
  return "uwsm-app -- " .. command
end

-- The command each function bind stands for, so the keybindings menu can still
-- run a bind that Hyprland only reports as Lua.
o.bind_commands = {}

-- The Lua expression each function bind stands for, for binds with no command
-- to run instead. The menu dispatches it as `hyprctl dispatch <expression>`.
o.bind_expressions = {}

-- Hand the launcher the focused window's pid, which it would otherwise ask
-- Hyprland for, to open the new terminal in that terminal's directory.
function o.launch_terminal()
  local function launch()
    local window = hl.get_active_window()
    if window and window.pid then
      hl.exec_cmd("nixos-launch-terminal --pid=" .. window.pid)
    else
      hl.exec_cmd("nixos-launch-terminal")
    end
  end

  o.bind_commands[launch] = "nixos-launch-terminal"
  return launch
end

function o.exec_on_start(command)
  hl.on("hyprland.start", function()
    hl.exec_cmd(command)
  end)
end

function o.launch_on_start(command)
  o.exec_on_start(o.launch(command))
end

function o.launch_webapp(url)
  return "nixos-launch-webapp " .. shell_quote(url)
end

function o.launch_webapp_sole(name, url)
  return "nixos-launch-or-focus-webapp " .. shell_quote(name) .. " " .. shell_quote(url)
end

function o.launch_sole(match, command)
  return "nixos-launch-or-focus " .. shell_quote(match) .. " " .. shell_quote(o.launch(command))
end

function o.bind_toggle(keys, description, toggle, options)
  o.bind(keys, description, "nixos-toggle-" .. toggle, options)
end

-- Bind one action to a key's press and another to its release, as for
-- push-to-talk. Hyprland skips a plain release bind once another key or mouse
-- button is released during the hold, or once the modifiers have changed, so
-- typing while holding the key would never run the release. The release half
-- here is transparent and ignores modifiers, and runs only after its own press
-- did, so letting go of the key without the rest of the chord does nothing. It
-- is also non-consuming: a release bind that ignores modifiers would otherwise
-- take the key from apps whenever it is pressed with other modifiers, such as
-- Shift+F9, or without them, such as a plain x for SUPER + X.
function o.bind_hold(keys, press_description, press, release_description, release, options)
  local held = false
  press, release = command_from(press, press_description), command_from(release, release_description)

  local function run(dispatcher)
    if type(dispatcher) == "string" then
      hl.exec_cmd(dispatcher)
    elseif type(dispatcher) == "function" then
      dispatcher()
    else
      hl.dispatch(dispatcher)
    end
  end

  local function on_press()
    held = true
    run(press)
  end

  local function on_release()
    if held then
      held = false
      run(release)
    end
  end

  if type(press) == "string" then
    o.bind_commands[on_press] = press
  end
  if type(release) == "string" then
    o.bind_commands[on_release] = release
  end

  local press_options, release_options = {}, {}
  for key, value in pairs(options or {}) do
    press_options[key], release_options[key] = value, value
  end
  -- Options that change when the press half fires would break the release half.
  for _, key in ipairs({ "repeating", "long_press", "click", "drag" }) do
    release_options[key] = nil
  end
  release_options.release, release_options.transparent = true, true
  release_options.ignore_mods, release_options.non_consuming = true, true

  o.bind(keys, press_description, on_press, press_options)
  o.bind(keys, release_description, on_release, release_options)
end

function o.notify(message)
  return "nixos-notification-send -u low " .. shell_quote(message)
end

-- What makes apps float on their own account, so a floating workspace can
-- leave their floating to them: the class and title patterns of rules that
-- float them, the tags rules float, and the patterns of rules that tag them.
o.floating_apps = { class = {}, title = {}, tags = {}, tagged = {} }
-- Helpers reload before workspace modes, so discard the previous config's hook.
o.floating_apps_changed = nil

function o.window(match, rules)
  local floating_changed = false
  rules.match = rules.match or {}

  if type(match) == "string" then
    rules.match.class = match
  else
    for key, value in pairs(match) do
      rules.match[key] = value
    end
  end

  if rules.float == true then
    -- Only a rule floating a tag alone floats everything with that tag; one
    -- that also names a class or title floats just those, recorded below.
    if type(rules.match.tag) == "string" and rules.match.class == nil and rules.match.title == nil then
      o.floating_apps.tags[rules.match.tag] = true
      floating_changed = true
    end
    for _, key in ipairs({ "class", "title" }) do
      if type(rules.match[key]) == "string" then
        table.insert(o.floating_apps[key], rules.match[key])
        floating_changed = true
      end
    end
  end

  if type(rules.tag) == "string" and rules.tag:sub(1, 1) == "+" then
    local tag = rules.tag:sub(2)
    o.floating_apps.tagged[tag] = o.floating_apps.tagged[tag] or {}
    for _, key in ipairs({ "class", "title" }) do
      if type(rules.match[key]) == "string" then
        table.insert(o.floating_apps.tagged[tag], { key = key, pattern = rules.match[key] })
        floating_changed = true
      end
    end
  end

  hl.window_rule(rules)
  if floating_changed and o.floating_apps_changed then
    o.floating_apps_changed()
  end
end

-- Opt a window in to NixOS's standard active/inactive transparency. The tag
-- lets Appearance > Windows > Window Opacity turn these windows opaque or glassy.
function o.transparent_window(match, opacity)
  o.window(match, { opacity = opacity or "0.985 0.96", tag = "+transparent-window" })
end
end

-- ----------------------------------------------------------------------------
-- default.hypr.input
-- ----------------------------------------------------------------------------
package.preload["default.hypr.input"] = function(...)
-- https://wiki.hypr.land/Configuring/Basics/Variables/#input

local keyboard = require("default.hypr.keyboard")

-- Layouts that can't type Latin letters. Keep in sync with the list in
-- etc/mkinitcpio.conf.d/nixos_hooks.conf.
local non_latin_layouts =
  " af am ara bd bg by et ge gr il in iq ir kg kh kz la lk mk mm mn mv np rs ru sy th tj ua "
-- us variants that can't type Latin letters either: Russian phonetic and Cherokee.
local non_latin_us_variants = " chr rus "

local vconsole = keyboard.selected()

local kb_layout = vconsole.XKBLAYOUT or "us"
local kb_variant = vconsole.XKBVARIANT or ""
-- Caps Lock is Caps Lock, and Shift + Caps Lock is the compose key. Stock XKB
-- has no such option, so NixOS defines it in /etc/xkb.
local kb_options = "nixos:shift_caps_compose"

-- Hyprland resolves keybindings against the first entry in kb_layout, not the
-- layout that's currently active, so NixOS's Latin-keysym bindings (SUPER + W
-- and friends) only fire when a Latin layout leads. Installing with a non-Latin
-- one would otherwise leave the desktop unusable.
if non_latin_layouts:find(" " .. kb_layout:match("^[^,]*") .. " ", 1, true) then
  -- Variants pair with layouts by position. A list that already names us (as in
  -- "ru,us") moves that entry and its variant to the front rather than gaining a
  -- second us, which would make the toggle cycle through a duplicate.
  local layouts, variants = {}, {}
  for layout in (kb_layout .. ","):gmatch("([^,]*),") do
    layouts[#layouts + 1] = layout
  end
  for variant in (kb_variant .. ","):gmatch("([^,]*),") do
    variants[#variants + 1] = variant
  end

  local us_variant = ""
  for i, layout in ipairs(layouts) do
    if layout == "us" and not non_latin_us_variants:find(" " .. (variants[i] or "") .. " ", 1, true) then
      us_variant = variants[i] or ""
      table.remove(layouts, i)
      if variants[i] then table.remove(variants, i) end
      break
    end
  end

  table.insert(layouts, 1, "us")
  table.insert(variants, 1, us_variant)
  kb_layout = table.concat(layouts, ",")
  kb_variant = table.concat(variants, ",")
  -- Reach the original layout with Left Alt + Right Alt.
  kb_options = kb_options .. ",grp:alts_toggle"
end

-- Saved selections already include their Latin-leading layout. Keep the
-- installer's layout-switching shortcut when a non-Latin layout remains.
if not kb_options:find("grp:alts_toggle", 1, true) then
  for layout in kb_layout:gmatch("[^,]+") do
    if non_latin_layouts:find(" " .. layout .. " ", 1, true) then
      kb_options = kb_options .. ",grp:alts_toggle"
      break
    end
  end
end

hl.config({
  input = {
    kb_layout = kb_layout,
    kb_variant = kb_variant,
    kb_model = "",
    kb_options = kb_options,
    kb_rules = "",
    follow_mouse = 1,
    sensitivity = 0,

    repeat_rate = 40,
    repeat_delay = 250,
    numlock_by_default = true,

    touchpad = {
      natural_scroll = false,
      clickfinger_behavior = true,
      scroll_factor = 0.4,
    },
  },

  misc = {
    key_press_enables_dpms = true,
    mouse_move_enables_dpms = true,
  },
})

-- Scroll nicely in the terminal. TUIs launched under their own app-id
-- (org.nixos.agent in the console, org.nixos.btop, TUI.float, ...) no longer
-- carry the terminal's class, but their initial title is still the terminal's
-- name, so they are matched by that to scroll at the same rate.
local function terminal_scroll(class, title, factor)
  o.window(class, { scroll_touchpad = factor })
  o.window({ class = "(org\\.nixos\\..*|TUI\\..*)", initial_title = title }, { scroll_touchpad = factor })
end

terminal_scroll("(Alacritty|kitty)", "(Alacritty|kitty)", 1.5)
-- foot only applies its scrollback multiplier to wheel clicks, not precise touchpad scrolling.
terminal_scroll("foot", "foot", 2.0)
terminal_scroll("com.mitchellh.ghostty", "Ghostty", 0.2)
end

-- ----------------------------------------------------------------------------
-- default.hypr.keyboard
-- ----------------------------------------------------------------------------
package.preload["default.hypr.keyboard"] = function(...)
-- The keyboard layout picked at install time. The installer and first-boot
-- setup persist it to /etc/vconsole.conf, so Hyprland reads it from there
-- instead of rewriting every user's config.

local keyboard = {}

local function read_values(path)
  local values = {}
  local file = io.open(path, "r")
  if not file then
    return values
  end

  for line in file:lines() do
    local key, value = line:match("^%s*([%w_]+)%s*=%s*(.-)%s*$")
    if key and value then
      value = value:gsub("%s+#.*$", "")
      value = value:gsub('^"(.*)"$', "%1")
      value = value:gsub("^'(.*)'$", "%1")
      values[key] = value
    end
  end

  file:close()
  return values
end

function keyboard.selected()
  local paths = require("default.hypr.paths")
  local values = read_values(paths.config_home .. "/nixos/keyboard-layouts")
  if values.XKBLAYOUT then return values end
  return keyboard.installed()
end

function keyboard.vconsole()
  return read_values("/etc/vconsole.conf")
end

-- Choices whose console keymap is plain US but whose desktop layout is not:
-- Korean keeps US letters, and Lao is non-Latin, so US still leads. Korean
-- installs take kr104, which adds Right Alt and Right Ctrl as 한/영 and 한자;
-- plain kr is what earlier installs saved.
local desktop_overrides = { kr = true, ["kr:kr104"] = true, la = true }

function keyboard.installed()
  local values = keyboard.vconsole()
  local override = read_values("/etc/nixos/input-method").XKB_LAYOUT
  if desktop_overrides[override]
    and (values.XKBLAYOUT or "us") == "us"
    and (values.XKBVARIANT or "") == "" then
    values.XKBLAYOUT, values.XKBVARIANT = override:match("^([^:]*):?(.*)$")
  end
  return values
end

-- Japanese (JIS) keyboards put +, ^, and the Henkan/Muhenkan keys where US
-- keyboards don't, so a few defaults only apply when that layout leads.
function keyboard.jis()
  local layout = keyboard.selected().XKBLAYOUT or "us"
  return layout:match("^[^,]*") == "jp"
end

return keyboard
end

-- ----------------------------------------------------------------------------
-- default.hypr.looknfeel
-- ----------------------------------------------------------------------------
package.preload["default.hypr.looknfeel"] = function(...)
-- Refer to https://wiki.hypr.land/Configuring/Basics/Variables/

local active_border_color = { colors = { "rgba(33ccffee)", "rgba(00ff99ee)" }, angle = 45 }
local inactive_border_color = "rgba(595959aa)"

hl.config({
  general = {
    gaps_in = 5,
    gaps_out = 10,
    border_size = 2,

    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },

    resize_on_border = true,
    extend_border_grab_area = 8,
    hover_icon_on_border = true,
    allow_tearing = false,
    layout = "dwindle",
  },

  decoration = {
    rounding = 0,

    shadow = {
      enabled = false,
    },

    blur = {
      enabled = false,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },

    groupbar = {
      font_size = 12,
      font_family = "monospace",
      font_weight_active = "ultraheavy",
      font_weight_inactive = "normal",
      indicator_height = 1,
      indicator_gap = 5,
      height = 22,
      gaps_in = 5,
      gaps_out = 0,
      text_color = "rgb(ffffff)",
      text_color_inactive = "rgba(ffffff90)",
      col = {
        active = "rgba(00000040)",
        inactive = "rgba(00000020)",
      },
      gradients = true,
      gradient_rounding = 0,
      gradient_round_only_edges = false,
    },
  },

  animations = {
    enabled = true,
  },
})

-- Default animations, see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Animations/
hl.curve("easeOutQuint", { type = "bezier", points = { { 0.23, 1 }, { 0.32, 1 } } })
hl.curve("easeInOutCubic", { type = "bezier", points = { { 0.65, 0.05 }, { 0.36, 1 } } })
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.curve("almostLinear", { type = "bezier", points = { { 0.5, 0.5 }, { 0.75, 1.0 } } })
hl.curve("quick", { type = "bezier", points = { { 0.15, 0 }, { 0.1, 1 } } })

hl.animation({ leaf = "global", enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "border", enabled = true, speed = 5.39, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows", enabled = true, speed = 3.79, bezier = "easeOutQuint" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4.1, bezier = "easeOutQuint", style = "popin 87%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.49, bezier = "linear", style = "popin 87%" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.73, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.46, bezier = "almostLinear" })
hl.animation({ leaf = "fade", enabled = true, speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "fadeSwitch", enabled = false })
hl.animation({ leaf = "layers", enabled = true, speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 4, bezier = "easeOutQuint", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.5, bezier = "linear", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1.79, bezier = "almostLinear" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.39, bezier = "almostLinear" })
hl.animation({ leaf = "workspaces", enabled = false })

hl.config({
  dwindle = {
    preserve_split = true,
    force_split = 2,
  },

  scrolling = {
    column_width = 0.49,
  },

  master = {
    new_status = "master",
  },

  misc = {
    disable_hyprland_logo = true,
    disable_splash_rendering = true,
    background_color = "rgb(000000)",
    disable_scale_notification = true,
    focus_on_activate = true,
    anr_missed_pings = 3,
    on_focus_under_fullscreen = 1,
    initial_workspace_tracking = 0,
    -- Let a fresh shell re-acquire the session lock after the lock client
    -- died, so nixos-restart-shell can recover the LOCK failsafe.
    allow_session_lock_restore = true,
  },

  cursor = {
    hide_on_key_press = true,
    warp_on_change_workspace = 1,
  },

  render = {
    -- Keep HDR displays in SDR when a window goes fullscreen. Auto-switching
    -- left SDR content looking washed out on the Pro Display XDR.
    cm_auto_hdr = 0,
  },

  binds = {
    hide_special_on_workspace_change = true,
  },
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.monitor-workspaces
-- ----------------------------------------------------------------------------
package.preload["default.hypr.monitor-workspaces"] = function(...)
-- Per-monitor workspaces: every monitor has its own workspaces 1-10, the way
-- Niri gives every output its own.
--
-- Hyprland numbers workspaces globally, so each monitor owns a block of ten:
-- the laptop panel 1-10, the next monitor 11-20, and so on. Super + 3 goes to
-- the third workspace in the focused monitor's block, and the bar labels each
-- monitor's workspaces 1-10.
--
-- A block belongs to the physical monitor, named by its make, model and serial.
-- The connector and Hyprland's monitor id would both be wrong: a dock renames
-- its connectors between plugs, and Hyprland hands a free id to whichever
-- display turns up next. The assignment lives in a state file, so a monitor
-- gets the same block every time it comes back, and the bar reads the same
-- file to know which block is its own.
--
-- Hyprland already moves an unplugged monitor's workspaces onto another one and
-- returns them when it comes back, as Niri does, but it recognizes the monitor
-- by its connector, and it puts a new monitor on the next free workspace number
-- rather than in its own block. Reconciling on every monitor change keeps each
-- monitor on its own block. Workspaces whose monitor is unplugged join the
-- block of the one they landed on, after its own, as Niri appends them to
-- another output, and a second state file remembers where each came from so it
-- goes back, under its old number, when that monitor returns. With no room in
-- the block they stay guests, and the bar lists them after the monitor's own.

local paths = require("default.hypr.paths")

local SLOTS = 10
local STATE_DIR = paths.state_home .. "/nixos"
local STATE_FILE = STATE_DIR .. "/monitor-workspaces"
local MERGED_FILE = STATE_DIR .. "/monitor-workspaces-merged"

local M = { slots = SLOTS }

-- Identity -> block, kept across sessions.
local blocks = {}
local written = nil

-- Connector -> identity for the monitors plugged in now.
local current = {}

local function load_blocks()
  local file = io.open(STATE_FILE, "r")
  if not file then
    return
  end

  for line in file:lines() do
    local block, connector, identity = line:match("^(%d+)\t([^\t]*)\t(.+)$")
    if block then
      blocks[identity] = tonumber(block)
      if connector ~= "" then
        current[connector] = identity
      end
    end
  end

  file:close()
end

load_blocks()

-- Workspace id -> where it came from, { id, identity }, for each workspace that
-- joined another monitor's block while its own monitor was unplugged. Kept in a
-- file to outlive config reloads, and cleared when Hyprland starts.
local merged = {}

local function load_merged()
  local file = io.open(MERGED_FILE, "r")
  if not file then
    return
  end

  for line in file:lines() do
    local id, original, identity = line:match("^(%d+)\t(%d+)\t(.+)$")
    if id then
      merged[tonumber(id)] = { id = tonumber(original), identity = identity }
    end
  end

  file:close()
end

load_merged()

local function save_merged()
  local ids = {}
  for id in pairs(merged) do
    ids[#ids + 1] = id
  end
  table.sort(ids)

  local lines = {}
  for _, id in ipairs(ids) do
    lines[#lines + 1] = id .. "\t" .. merged[id].id .. "\t" .. merged[id].identity .. "\n"
  end

  local file = io.open(MERGED_FILE, "w")
  if not file then
    os.execute("mkdir -p " .. o.shell_quote(STATE_DIR))
    file = io.open(MERGED_FILE, "w")
  end

  if file then
    file:write(table.concat(lines))
    file:close()
  end
end

-- One line per monitor ever seen: its block, its connector while it is plugged
-- in, and its identity. The bar maps its own connector to a block from this.
local function save(monitors, identities)
  local connector = {}
  for _, monitor in ipairs(monitors) do
    connector[identities[monitor.name]] = monitor.name
  end

  local rows = {}
  for identity, block in pairs(blocks) do
    rows[#rows + 1] = { block = block, line = block .. "\t" .. (connector[identity] or "") .. "\t" .. identity }
  end
  table.sort(rows, function(left, right) return left.block < right.block end)

  local lines = {}
  for _, row in ipairs(rows) do
    lines[#lines + 1] = row.line
  end
  local content = table.concat(lines, "\n") .. "\n"

  if content == written then
    return
  end

  local file = io.open(STATE_FILE, "w")
  if not file then
    os.execute("mkdir -p " .. o.shell_quote(STATE_DIR))
    file = io.open(STATE_FILE, "w")
  end

  if file then
    file:write(content)
    file:close()
    written = content
  end
end

local function internal(monitor)
  return monitor.name:match("^eDP") or monitor.name:match("^LVDS") or monitor.name:match("^DSI")
end

-- The monitors that show workspaces of their own. `gone` names one Hyprland
-- still lists while it reports the monitor's removal.
local function connected(gone)
  local monitors = {}

  for _, monitor in ipairs(hl.get_monitors()) do
    if not monitor.is_mirror and monitor.name ~= gone then
      monitors[#monitors + 1] = monitor
    end
  end

  -- The laptop panel claims the first block, so a laptop keeps 1-10 on its own
  -- screen whatever is plugged in.
  table.sort(monitors, function(left, right)
    if (internal(left) ~= nil) ~= (internal(right) ~= nil) then
      return internal(left) ~= nil
    end
    return left.id < right.id
  end)

  return monitors
end

-- Make, model and serial. Two monitors that report the same, such as a pair
-- without serials, are told apart by connector order when they first appear,
-- and each keeps that identity while it stays plugged in, so unplugging one of
-- the pair doesn't hand its block to the other.
local function identities_of(monitors)
  local identities = {}
  local taken = {}

  local function described(monitor)
    local description = monitor.description or ""
    return description ~= "" and description or monitor.name
  end

  for _, monitor in ipairs(monitors) do
    local identity = current[monitor.name]
    if identity and not taken[identity] and identity:gsub(" #%d+$", "") == described(monitor) then
      identities[monitor.name] = identity
      taken[identity] = true
    end
  end

  local ordered = {}
  for _, monitor in ipairs(monitors) do
    ordered[#ordered + 1] = monitor
  end
  table.sort(ordered, function(left, right) return left.name < right.name end)

  for _, monitor in ipairs(ordered) do
    if not identities[monitor.name] then
      local identity = described(monitor)
      local count = 1
      while taken[identity] do
        count = count + 1
        identity = described(monitor) .. " #" .. count
      end
      identities[monitor.name] = identity
      taken[identity] = true
    end
  end

  current = identities

  return identities
end

local function free_block()
  local taken = {}
  for _, block in pairs(blocks) do
    taken[block] = true
  end

  local block = 0
  while taken[block] do
    block = block + 1
  end

  return block
end

-- Each connected monitor's block, assigning one to a monitor seen for the first
-- time. Keyed by connector.
local function assign(monitors)
  local identities = identities_of(monitors)
  local by_connector = {}

  for _, monitor in ipairs(monitors) do
    local identity = identities[monitor.name]
    if not blocks[identity] then
      blocks[identity] = free_block()
    end
    by_connector[monitor.name] = blocks[identity]
  end

  save(monitors, identities)

  return by_connector, identities
end

local function block_of_id(id)
  return (id - 1) // SLOTS
end

local function identity_of_block(block)
  for identity, owned in pairs(blocks) do
    if owned == block then
      return identity
    end
  end

  return nil
end

-- Give a workspace another id, carrying where it came from with it.
local function renumber(workspace, id)
  local old = workspace.id
  hl.dispatch(hl.dsp.workspace.change_id({ workspace = tostring(old), id = id }))

  -- A record left under the new id belonged to a workspace that has gone.
  if merged[old] or merged[id] then
    merged[id] = merged[old]
    merged[old] = nil
    save_merged()
  end
end

local function owner(id, monitors, by_connector)
  if id < 1 then
    return nil
  end

  for _, monitor in ipairs(monitors) do
    if by_connector[monitor.name] == block_of_id(id) then
      return monitor
    end
  end

  return nil
end

local function regular(workspace)
  return workspace and not workspace.special and workspace.id > 0
end

-- The workspace id of a slot on a monitor.
function M.workspace_id(monitor, slot)
  local by_connector = assign(connected())
  return (by_connector[monitor.name] or 0) * SLOTS + slot
end

-- The workspace a monitor falls back to when what it shows isn't its own: the
-- lowest of its own already on it, or its first.
local function home(monitor, block)
  local best = nil

  for _, workspace in ipairs(hl.get_workspaces()) do
    if regular(workspace) and block_of_id(workspace.id) == block and workspace.monitor
      and workspace.monitor.name == monitor.name and (not best or workspace.id < best) then
      best = workspace.id
    end
  end

  return best or block * SLOTS + 1
end

-- Show a workspace on a monitor, bringing it over from another or creating it
-- there. Bringing it over is a move rather than a focus on the current monitor,
-- which swaps the two monitors' workspaces when it is visible over there.
local function show(monitor, id)
  local workspace = hl.get_workspace(id)

  if workspace and workspace.monitor and workspace.monitor.name ~= monitor.name then
    hl.dispatch(hl.dsp.workspace.move({ workspace = tostring(id), monitor = monitor.name }))
    workspace = hl.get_workspace(id)
  end

  if workspace then
    monitor:set_workspace({ workspace = workspace.name })
  else
    hl.dispatch(hl.dsp.focus({ monitor = monitor.name }))
    hl.dispatch(hl.dsp.focus({ workspace = tostring(id) }))
  end
end

-- Moving a monitor's visible workspace away leaves Hyprland to fill the gap
-- with any workspace it finds, or a fresh one with the lowest free number, so
-- put the monitor back on one of its own.
local function settle(monitor, monitors, by_connector)
  local block = by_connector[monitor.name]
  local active = monitor.active_workspace

  if block and regular(active) and block_of_id(active.id) ~= block and owner(active.id, monitors, by_connector) then
    show(monitor, home(monitor, block))
  end
end

-- Bring a workspace of this monitor's block back from wherever an unplug left
-- it. Moving it explicitly, rather than focusing it on the current monitor,
-- keeps Hyprland from swapping the two monitors' workspaces when it is visible
-- over there.
local function reclaim(monitor, id)
  local workspace = hl.get_workspace(id)
  if not workspace or not workspace.monitor or workspace.monitor.name == monitor.name then
    return
  end

  local away = workspace.monitor
  hl.dispatch(hl.dsp.workspace.move({ workspace = tostring(id), monitor = monitor.name }))

  local monitors = connected()
  settle(away, monitors, assign(monitors))
end

-- Renumber a workspace into a block, keeping its slot when that one is free and
-- taking the first free one otherwise. False when all ten are taken.
local function adopt(workspace, block)
  local wanted = block * SLOTS + (workspace.id - 1) % SLOTS + 1
  local candidates = { wanted }
  for slot = 1, SLOTS do
    candidates[#candidates + 1] = block * SLOTS + slot
  end

  for _, id in ipairs(candidates) do
    if not hl.get_workspace(id) then
      renumber(workspace, id)
      return true
    end
  end

  return false
end

-- The first free id after the highest of a block in use, as Niri appends an
-- unplugged output's workspaces after another's, or any free one in the block
-- when the last is taken. Nil when all ten are.
local function append_slot(block)
  local highest = block * SLOTS
  for _, workspace in ipairs(hl.get_workspaces()) do
    if regular(workspace) and block_of_id(workspace.id) == block and workspace.id > highest then
      highest = workspace.id
    end
  end

  if highest < block * SLOTS + SLOTS then
    return highest + 1
  end

  for id = block * SLOTS + 1, block * SLOTS + SLOTS do
    if not hl.get_workspace(id) then
      return id
    end
  end

  return nil
end

local function target_monitor(name)
  if name then
    return hl.get_monitor(name)
  end

  return hl.get_active_monitor()
end

-- Bind actions return functions for hl.dispatch, so `hyprctl dispatch
-- 'o.workspaces.focus(3)'` runs the same thing as the key. The keybindings menu
-- replays a bind through that expression.
local function action(fn, expression)
  o.bind_expressions[fn] = expression
  return fn
end

local function literal(value)
  if value == nil then
    return "nil"
  end
  return string.format("%q", value)
end

-- Go to a slot on a monitor, the focused one unless named.
function M.focus(slot, monitor_name)
  return action(function()
    local monitor = target_monitor(monitor_name)
    if not monitor then
      return
    end

    if not monitor.focused then
      hl.dispatch(hl.dsp.focus({ monitor = monitor.name }))
    end

    local id = M.workspace_id(monitor, slot)
    reclaim(monitor, id)
    hl.dispatch(hl.dsp.focus({ workspace = tostring(id) }))
  end, "o.workspaces.focus(" .. slot .. (monitor_name and ", " .. literal(monitor_name) or "") .. ")")
end

-- Move the active window to a slot on the focused monitor, following it unless
-- `follow` is false.
function M.move_window(slot, follow)
  return action(function()
    local window = hl.get_active_window()
    local monitor = hl.get_active_monitor()
    if not window or not monitor then
      return
    end

    local id = M.workspace_id(monitor, slot)
    reclaim(monitor, id)
    hl.dispatch(hl.dsp.window.move({ workspace = tostring(id), follow = follow ~= false, window = "address:" .. window.address }))
  end, "o.workspaces.move_window(" .. slot .. (follow == false and ", false" or "") .. ")")
end

-- Move the active workspace to the monitor in a direction, where it joins that
-- monitor's block, under the same number when it is free. With all ten taken it
-- keeps its number and stays a guest until its own monitor wants it back.
function M.move_to_monitor(direction)
  return action(function()
    local workspace = hl.get_active_workspace()
    if not regular(workspace) then
      return
    end

    -- Hyprland reports a move toward no monitor as an error on screen.
    local target = hl.get_monitor(direction)
    if not target then
      return
    end

    local id = workspace.id
    local from = hl.get_active_monitor()
    hl.dispatch(hl.dsp.workspace.move({ monitor = target.name }))

    local moved = hl.get_workspace(id)
    if not moved or not moved.monitor or (from and moved.monitor.name == from.name) then
      return
    end

    -- Moved by hand, it belongs where it was put, as in Niri.
    if merged[id] then
      merged[id] = nil
      save_merged()
    end

    local monitors = connected()
    local by_connector = assign(monitors)
    local block = by_connector[moved.monitor.name]
    if block and block_of_id(id) ~= block then
      adopt(moved, block)
    end
    if from then
      settle(from, monitors, by_connector)
    end

    -- Settling the monitor it left can take focus; it belongs with the
    -- workspace that moved.
    hl.dispatch(hl.dsp.focus({ workspace = tostring(moved.id) }))
  end, "o.workspaces.move_to_monitor(" .. literal(direction) .. ")")
end

-- Move the focused window onto the workspace the monitor in that direction
-- shows, and follow it there.
function M.move_window_to_monitor(direction)
  return action(function()
    local target = hl.get_monitor(direction)
    if target then
      hl.dispatch(hl.dsp.window.move({ monitor = target.name }))
    end
  end, "o.workspaces.move_window_to_monitor(" .. literal(direction) .. ")")
end

-- Put every workspace whose monitor is plugged in back on it, and every monitor
-- on a workspace of its own. `added` names a monitor that just arrived, which
-- leaves whatever Hyprland put it on; `gone` one being removed.
function M.reconcile(added, gone)
  local monitors = connected(gone)
  if #monitors == 0 then
    return
  end

  local by_connector, identities = assign(monitors)
  local focused_window = hl.get_active_window()
  local focused_monitor = hl.get_active_monitor()
  local focused_name = focused_monitor and focused_monitor.name
  local changed = false

  local function own_views()
    for _, monitor in ipairs(monitors) do
      local block = by_connector[monitor.name]
      local active = monitor.active_workspace
      local own = regular(active) and block_of_id(active.id) == block

      -- A workspace whose monitor is unplugged stays in view where it was put,
      -- unless this monitor has only just arrived on it. An empty one is only
      -- the number Hyprland starts a monitor on.
      local guest = regular(active) and not owner(active.id, monitors, by_connector) and monitor.name ~= added
        and (active.windows or 0) > 0

      if not own and not guest then
        show(monitor, home(monitor, block))
        changed = true
      end
    end
  end

  -- A workspace sitting on a monitor other than the plugged-in one that owns it
  -- goes home when a monitor arrives, since that is a monitor returning to the
  -- workspaces an unplug left elsewhere. Otherwise it is one that got there some
  -- other way, such as a session from before workspaces were per monitor or a
  -- window rule naming a number, and it joins the block of the monitor it is
  -- on, so its windows don't jump screens. An empty one is only the number
  -- Hyprland parked a monitor on, and goes away once the monitor shows its own.
  local function place()
    for _, workspace in ipairs(hl.get_workspaces()) do
      if regular(workspace) and workspace.monitor and (workspace.windows or 0) > 0 then
        local home_monitor = owner(workspace.id, monitors, by_connector)
        if home_monitor and home_monitor.name ~= workspace.monitor.name then
          local here = by_connector[workspace.monitor.name]
          if added or not here or not adopt(workspace, here) then
            hl.dispatch(hl.dsp.workspace.move({ workspace = tostring(workspace.id), monitor = home_monitor.name }))
          end
          changed = true
        end
      end
    end
  end

  -- Workspaces that joined another monitor's block while theirs was unplugged
  -- go back to it, under their old numbers when those are free.
  local function restore()
    local ids = {}
    for id in pairs(merged) do
      ids[#ids + 1] = id
    end
    table.sort(ids)

    for _, id in ipairs(ids) do
      local origin = merged[id]
      local monitor = nil
      for _, candidate in ipairs(monitors) do
        if identities[candidate.name] == origin.identity then
          monitor = candidate
        end
      end

      if monitor then
        merged[id] = nil
        save_merged()

        local workspace = hl.get_workspace(id)
        if regular(workspace) then
          if not workspace.monitor or workspace.monitor.name ~= monitor.name then
            hl.dispatch(hl.dsp.workspace.move({ workspace = tostring(id), monitor = monitor.name }))
          end

          if block_of_id(origin.id) == by_connector[monitor.name] and not hl.get_workspace(origin.id) then
            renumber(workspace, origin.id)
          elseif block_of_id(id) ~= by_connector[monitor.name] then
            adopt(workspace, by_connector[monitor.name])
          end
          changed = true
        end
      end
    end
  end

  -- A workspace whose monitor is unplugged joins the block of the monitor it
  -- waits on, after that monitor's own, and remembers where it came from. An
  -- empty one is left to go away, and one with no room stays a guest.
  local function merge()
    local guests = {}
    for _, workspace in ipairs(hl.get_workspaces()) do
      if regular(workspace) and workspace.monitor and (workspace.windows or 0) > 0
        and not owner(workspace.id, monitors, by_connector) and by_connector[workspace.monitor.name] then
        guests[#guests + 1] = workspace
      end
    end
    table.sort(guests, function(left, right) return left.id < right.id end)

    for _, workspace in ipairs(guests) do
      local old = workspace.id
      local id = append_slot(by_connector[workspace.monitor.name])
      if id then
        -- One merged before keeps the monitor it first came from.
        local origin = merged[old]
        local identity = identity_of_block(block_of_id(old))
        if not origin and identity then
          merged[old] = { id = old, identity = identity }
        end
        renumber(workspace, id)
        save_merged()
        changed = true
      end
    end
  end

  restore()

  -- Views first for a new monitor, so the number Hyprland gave it is left empty
  -- and goes away instead of being carried to the monitor that owns it.
  if added then
    own_views()
  end
  place()
  merge()

  -- Moving a visible workspace home leaves a gap Hyprland fills with anything.
  own_views()

  if changed then
    if focused_window and hl.get_window("address:" .. focused_window.address) then
      hl.dispatch(hl.dsp.focus({ window = "address:" .. focused_window.address }))
    elseif focused_name and focused_name ~= gone and hl.get_monitor(focused_name) then
      hl.dispatch(hl.dsp.focus({ monitor = focused_name }))
    end
  end
end

hl.on("hyprland.start", function()
  -- Windows don't outlive a session, so neither do the workspaces that held them.
  merged = {}
  save_merged()
  M.reconcile()
end)

-- A workspace created under a remembered number is a new one; the one that
-- came from elsewhere has gone.
hl.on("workspace.created", function(workspace)
  if workspace and merged[workspace.id] then
    merged[workspace.id] = nil
    save_merged()
  end
end)

hl.on("config.reloaded", function()
  M.reconcile()
end)

hl.on("monitor.added", function(monitor)
  M.reconcile(monitor and monitor.name)
end)

-- Hyprland reports the removal from inside the monitor's teardown, where moving
-- workspaces or focus onto a monitor that was mirroring it crashes Hyprland, so
-- reconcile once the teardown has returned.
hl.on("monitor.removed", function(monitor)
  local name = monitor and monitor.name
  hl.timer(function()
    M.reconcile(nil, name)
  end, { type = "oneshot", timeout = 1 })
end)

o.workspaces = M

return M
end

-- ----------------------------------------------------------------------------
-- default.hypr.nixos
-- ----------------------------------------------------------------------------
package.preload["default.hypr.nixos"] = function(...)
-- NixOS Hyprland setup: helpers, defaults, and current theme overrides.

require("default.hypr.helpers")
local require_optional = require("default.hypr.require_optional")

-- Use NixOS defaults, but don't edit these directly.
require("default.hypr.autostart")
require("default.hypr.monitor-workspaces")
if _G.nixos_default_bindings ~= false then
  require("default.hypr.bindings.media")
  require("default.hypr.bindings.clipboard")
  require("default.hypr.bindings.input-method")
  require("default.hypr.bindings.jis")
  require("default.hypr.bindings.tiling")
  require("default.hypr.bindings.utilities")
  require("default.hypr.bindings.dictation")
  require_optional.module("default.hypr.bindings.applications")
end
require("default.hypr.envs")
require("default.hypr.looknfeel")
require("default.hypr.qconsole")
require("default.hypr.input")
require("default.hypr.windows")
require("default.hypr.pop")
require("default.hypr.dictation-backend")

-- Current theme overrides.
require_optional.module("nixos.current.theme.hyprland")
end

-- ----------------------------------------------------------------------------
-- default.hypr.nvidia
-- ----------------------------------------------------------------------------
package.preload["default.hypr.nvidia"] = function(...)
local paths = require("default.hypr.paths")

local nvidia = paths.nixos_path .. "/bin/nixos-hw-nvidia"
local nvidia_display = paths.nixos_path .. "/bin/nixos-hw-nvidia-display"
local nvidia_gsp = paths.nixos_path .. "/bin/nixos-hw-nvidia-gsp"
local nvidia_without_gsp = paths.nixos_path .. "/bin/nixos-hw-nvidia-without-gsp"

-- These detectors read cached sysfs IDs rather than shelling out to lspci.
-- lspci reads PCI config space, which resumes a runtime-suspended GPU, and on a
-- hybrid laptop that wake alone outlasts Hyprland's 1.5s config reload budget.
if o.shell_succeeds(o.shell_quote(nvidia)) then
  -- On hybrid laptops the display is wired to the iGPU, so forcing NVIDIA's
  -- VA-API/GLX drivers globally breaks Chromium-based browsers (black video).
  -- Only apply those when NVIDIA actually drives the display.
  local nvidia_is_display = o.shell_succeeds(o.shell_quote(nvidia_display))
  if o.shell_succeeds(o.shell_quote(nvidia_gsp)) then
    hl.env("NVD_BACKEND", "direct")
    if nvidia_is_display then
      hl.env("LIBVA_DRIVER_NAME", "nvidia")
      hl.env("__GLX_VENDOR_LIBRARY_NAME", "nvidia")
    end
  elseif o.shell_succeeds(o.shell_quote(nvidia_without_gsp)) then
    hl.env("NVD_BACKEND", "egl")
    if nvidia_is_display then
      hl.env("__GLX_VENDOR_LIBRARY_NAME", "nvidia")
    end
  end
end
end

-- ----------------------------------------------------------------------------
-- default.hypr.paths
-- ----------------------------------------------------------------------------
package.preload["default.hypr.paths"] = function(...)
-- Shared path constants for NixOS's Hyprland Lua modules.
-- Lua files loaded with require() have separate local scopes, so modules that
-- need these paths import this table instead of repeating os.getenv() lookups.

local home = os.getenv("HOME")

-- A variable that is set but empty means "unset" (XDG Base Directory spec);
-- bash's ${VAR:-fallback} in the sibling tools treats it the same way.
local function env_or(name, fallback)
  local value = os.getenv(name)
  if value == nil or value == "" then
    return fallback
  end
  return value
end

return {
  home = home,
  config_home = env_or("XDG_CONFIG_HOME", home .. "/.config"),
  state_home = env_or("XDG_STATE_HOME", home .. "/.local/state"),
  nixos_path = env_or("NIXOS_PATH", "/usr/share/nixos"),
}
end

-- ----------------------------------------------------------------------------
-- default.hypr.pop
-- ----------------------------------------------------------------------------
package.preload["default.hypr.pop"] = function(...)
-- Hyprland moves a floating window to another monitor at the same offset from its origin,
-- so a popped-out window (Super+O) would land off-center or off a smaller screen.

local function popped(window)
  for _, tag in ipairs(window.tags or {}) do
    if tag == "pop" then
      return true
    end
  end

  return false
end

-- A dispatcher move fires this before the window lands, while window.monitor is still
-- the one it is leaving, so the center waits a loop. A mouse drag has already landed.
hl.on("window.move_to_workspace", function(window, workspace)
  if not (window and workspace and window.monitor and workspace.monitor) then return end
  if window.monitor.id == workspace.monitor.id or not popped(window) then return end

  local target = "address:" .. window.address
  hl.timer(function()
    hl.dispatch(hl.dsp.window.center({ window = target }))
  end, { timeout = 1, type = "oneshot" })
end)
end

-- ----------------------------------------------------------------------------
-- default.hypr.qconsole
-- ----------------------------------------------------------------------------
package.preload["default.hypr.qconsole"] = function(...)
-- The Quake console: a dimmed overlay that drops down over whatever workspace
-- you are on. It is its own special workspace, separate from the full-size
-- scratchpad on Super + S. Its bindings live in bindings/tiling.lua, and its
-- slide is animated below.

-- How much of the usable screen the console covers, measured from the top.
local share = 0.5

-- A console holding a single window is boxed into a centered panel this many
-- times wider than it is tall, rather than stretched the width of the screen.
-- A second app on the console gets the full width back: two windows splitting
-- a half-width column is worse than the band this replaced.
local box = 2

local CONSOLE = "special:qconsole"

-- Seed the console with the default agent the first time it opens, rather than
-- at boot, so nothing is running until it is wanted. The exec rule has to pin
-- the workspace itself: Hyprland only tags a spawn with the workspace it came
-- from while misc.initial_workspace_tracking is on, and looknfeel turns it off.
-- NixOS ships without a default agent, and nixos-agent exits without
-- opening anything when none is set, so until one is picked this just opens an
-- empty console. A console created by moving a window onto it is not empty, and
-- is left alone.
hl.on("workspace.created", function(ws)
  if ws and ws.name == CONSOLE and ws.is_empty then
    hl.exec_cmd("nixos-agent", { workspace = CONSOLE .. " silent" })
  end
end)

-- Dimming only applies while a special workspace is open, so the console gets
-- its separation from the workspace underneath without costing anything the
-- rest of the time.
hl.config({
  decoration = {
    dim_special = 0.6,
  },
})

-- The panel is always flush with the top and always centered, so two numbers
-- describe it: the gap down each side and the gap underneath.
--
-- Refitting replaces the rule in place rather than stacking a new one, but it
-- still schedules a monitor and window state refresh, and monitor.focused fires
-- on every hop between screens. Most of those hops do not change the gaps, so
-- only write the rule when it actually moves.
local beside, below = nil, nil

local function cover(side, bottom)
  if beside == side and below == bottom then
    return false
  end
  beside, below = side, bottom

  hl.workspace_rule({
    workspace = CONSOLE,
    gaps_in = 0,
    gaps_out = { top = 0, right = side, bottom = bottom, left = side },

    -- Nothing to highlight in a console that is only ever focused when it is
    -- open, and the active border reads as a stray frame around a panel that
    -- is already set apart by the dimming behind it.
    no_border = true,
  })

  return true
end

-- One window reads as a console and gets the panel. A second app has turned the
-- console into a workspace, and a workspace wants the whole width. Only tiled
-- windows count: the gaps are what size the panel, and a floating window on top
-- of the console is not laid out by them.
local function alone()
  local tiled = 0
  for _, window in ipairs(hl.get_workspace_windows(CONSOLE)) do
    if not window.floating then
      tiled = tiled + 1
    end
  end
  return tiled <= 1
end

-- Sizing the console with a window rule would freeze it at whatever the screen
-- measured when it first opened, because Hyprland resolves those expressions
-- once, as the window maps. Rescaling the monitor afterwards would leave a
-- console that is no longer half of anything. Gaps are re-applied by the layout
-- instead, so the console is sized by the area left around it, and that area is
-- recomputed whenever the monitor it opens on changes.
local function fit(monitor)
  -- A monitor handle whose output has gone away answers nil to every field, and
  -- layout changes are exactly when that happens, so this also covers reading
  -- width, height and reserved below.
  if not monitor or not monitor.scale or monitor.scale <= 0 then
    return false
  end

  -- Width and height are the panel's own pixels, so a monitor turned on its
  -- side still reports them the way the panel is built. The odd transforms are
  -- the quarter turns, and those are the ones that swap the work area.
  local width, height = monitor.width, monitor.height
  if monitor.transform % 2 == 1 then
    width, height = height, width
  end

  -- Monitor dimensions are in physical pixels; gaps are logical, so the scale
  -- has to come out before the reserved area (already logical) comes off.
  -- reserved бывает nil до первой раскладки (видно в VM при старте сессии)
  local reserved = monitor.reserved or {}
  height = height / monitor.scale - (reserved.top or 0) - (reserved.bottom or 0)
  width = width / monitor.scale - (reserved.left or 0) - (reserved.right or 0)

  local tall = math.floor(height * share)
  local wide = width
  if alone() then
    wide = math.min(width, tall * box)
  end

  return cover(math.floor((width - wide) / 2), math.floor(height - tall))
end

-- The console keeps the geometry of the output it is open on: a follow_mouse hop
-- onto another screen must not resize a console that is already showing. While
-- it is hidden there is nothing to size but the output that will show it next.
local function console_monitor()
  local ws = hl.get_workspace(CONSOLE)
  local mon = ws and ws.visible and ws.monitor

  if mon and mon.scale and mon.scale > 0 then
    return mon
  end

  return hl.get_active_monitor()
end

local function refit(monitor)
  if fit(monitor or console_monitor()) then
    -- Land the new gaps in this pass rather than a frame later, so the console
    -- does not visibly resize itself once it has already dropped down.
    hl.exec_scheduled_prop_refresh_immediately()
  end
end

-- Until a monitor can be read, cover the whole work area rather than leaving
-- the console unruled, so it is never seeded without its placement. A reload
-- runs this again with the console already on screen, so it starts from the
-- output the console is on rather than whichever one the pointer is over.
cover(0, 0)
fit(console_monitor())

hl.on("monitor.layout_changed", function()
  refit()
end)

hl.on("monitor.focused", function()
  refit()
end)

-- Special workspaces open on the monitor they are toggled on, not on whichever
-- output last happened to be focused when the rule was written, so these two
-- take the monitor they are handed rather than looking one up.
hl.on("workspace.special_active", function(ws, mon)
  if ws and ws.name == CONSOLE then
    refit(mon)
  end
end)

hl.on("workspace.move_to_monitor", function(ws, mon)
  if ws and ws.name == CONSOLE then
    refit(mon)
  end
end)

-- The panel is only centered while the console holds one tiled window, so the
-- count has to be rechecked as apps come and go: opened and closed, moved on or
-- off (Super+Shift+Grave, Super+Shift+1), and floated or tiled (Super+T, Super+O).
-- window.close is left out, since it still counts the window on its way out and
-- window.destroy follows it anyway. Measured on Hyprland 0.56.2, a move is
-- trailed by several window.update_rules, as is a float toggle, and the last of
-- those always reads the settled count; the earlier ones refit to what the rule
-- already is, which cover() skips.
--
-- Only while it is on screen, though. A hidden console is refitted on its way in
-- by workspace.special_active, and every window opened anywhere on the desktop
-- would otherwise rewrite the rule.
local function recount()
  local ws = hl.get_workspace(CONSOLE)
  if ws and ws.visible then
    refit()
  end
end

hl.on("window.open", recount)
hl.on("window.destroy", recount)
hl.on("window.move_to_workspace", recount)
hl.on("window.update_rules", recount)

-- The direction names the edge the offset is measured from, not where the
-- workspace goes: "slide top" drops it down into view, and "slide bottom"
-- retracts it back up the way a Quake console does.
hl.animation({ leaf = "specialWorkspaceIn", enabled = true, speed = 3, bezier = "easeOutQuint", style = "slide top" })
hl.animation({ leaf = "specialWorkspaceOut", enabled = true, speed = 2, bezier = "easeInOutCubic", style = "slide bottom" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.require_all
-- ----------------------------------------------------------------------------
package.preload["default.hypr.require_all"] = function(...)
-- Require every *.lua file in a directory in sorted order.
-- Used for NixOS extension-style folders such as default/hypr/apps,
-- default/hypr/bindings, and ~/.local/state/nixos/toggles/hypr.
-- Pass a module prefix for normal package.path modules, e.g.
--   require_all.files(paths.nixos_path .. "/default/hypr/apps", "default.hypr.apps")
-- Pass nil as the prefix when the directory itself has been added to package.path.
-- Pass options.exclude as a set of base names (without ".lua") to skip; a legacy
-- file that must never be loaded as code stays on disk for a migration to remove.

local M = {}

local function shell_quote(path)
  return "'" .. path:gsub("'", "'\\''") .. "'"
end

function M.files(dir, module_prefix, options)
  local exclude = options and options.exclude or {}
  local handle = io.popen("find " .. shell_quote(dir) .. " -maxdepth 1 -type f -name '*.lua' -printf '%f\\n' 2>/dev/null | sort")
  if handle then
    for filename in handle:lines() do
      local name = filename:gsub("%.lua$", "")
      if not exclude[name] then
        local module = name
        if module_prefix then
          module = module_prefix .. "." .. module
        end

        if options and options.reload then
          package.loaded[module] = nil
        end

        require(module)
      end
    end
    handle:close()
  end
end

return M
end

-- ----------------------------------------------------------------------------
-- default.hypr.require_optional
-- ----------------------------------------------------------------------------
package.preload["default.hypr.require_optional"] = function(...)
-- Require a module only when it can be found on package.path.
-- Errors inside existing modules still surface normally.

local M = {}

function M.module(module)
  if package.searchpath(module, package.path) then
    return require(module)
  end
end

return M
end

-- ----------------------------------------------------------------------------
-- default.hypr.startup-cursor
-- ----------------------------------------------------------------------------
package.preload["default.hypr.startup-cursor"] = function(...)
local function cursor_theme(value)
  if value and value ~= "" and value ~= "nixos-startup" then return value end
end

local function normal_theme(interrupted)
  local current = os.getenv("XCURSOR_THEME")
  local theme = cursor_theme(current)
  -- Only a lost preference needs recovering; an unset theme still means the default alias.
  if theme or not (interrupted or current == "nixos-startup") then return theme or "default" end
  theme = cursor_theme(os.getenv("NIXOS_STARTUP_CURSOR_THEME"))
  if theme then return theme end
  local pipe = io.popen("gsettings get org.gnome.desktop.interface cursor-theme 2>/dev/null", "r")
  if pipe then
    theme = cursor_theme((pipe:read("*a") or ""):match("^'(.-)'%s*$"))
    pipe:close()
  end
  return theme or "default"
end

local function normal_path()
  local kept = {}
  for entry in (os.getenv("XCURSOR_PATH") or "~/.local/share/icons:~/.icons:/usr/share/icons:/usr/share/pixmaps"):gmatch("[^:]+") do
    if not entry:match("/default/hypr/cursors$") then table.insert(kept, entry) end
  end
  return table.concat(kept, ":")
end

-- Hyprland polls cursor.invisible, so its first frames need a blank cursor too.
function nixos_startup_cursor_restore(loaded)
  if not nixos_startup_cursor_pending then return end
  local cursor = nixos_startup_cursor
  if loaded then
    nixos_startup_cursor_pending = false
    hl.env("NIXOS_STARTUP_CURSOR_SESSION", "")
    hl.env("NIXOS_STARTUP_CURSOR_THEME", "")
    hl.config({ cursor = cursor.config })
    if cursor.config.enable_hyprcursor and cursor.hyprcursor then
      hl.exec_cmd("hyprctl setcursor " .. o.shell_quote(cursor.hyprcursor) .. " " .. cursor.size)
    end
    hl.exec_cmd("xsetroot -cursor_name left_ptr >/dev/null 2>&1 || true")
  elseif not cursor.restoring then
    -- Reload the normal Xcursor fallback before enabling Hyprcursor or GSettings.
    cursor.restoring = true
    hl.env("XCURSOR_PATH", cursor.path)
    hl.env("XCURSOR_THEME", cursor.xcursor)
    hl.exec_cmd("dbus-update-activation-environment --systemd XCURSOR_PATH XCURSOR_THEME")
    local complete = "if nixos_startup_cursor and nixos_startup_cursor.xcursor == " .. string.format("%q", cursor.xcursor)
      .. " and nixos_startup_cursor.size == " .. cursor.size .. " then nixos_startup_cursor_restore(true) end"
    hl.exec_cmd("hyprctl setcursor " .. o.shell_quote(cursor.xcursor) .. " " .. cursor.size
      .. " && hyprctl eval " .. o.shell_quote(complete))
  end
end

hl.on("config.reloaded", function()
  local recover = false
  if nixos_startup_cursor_pending == nil then
    -- An ordinary reload must not hide the pointer, but an interrupted reveal survives.
    local cold = #hl.get_monitors() == 0
    local session = os.getenv("HYPRLAND_INSTANCE_SIGNATURE")
    local interrupted = session and os.getenv("NIXOS_STARTUP_CURSOR_SESSION") == session
    recover = not cold and not interrupted and os.getenv("XCURSOR_THEME") == "nixos-startup"
    nixos_startup_cursor_pending = cold or interrupted or recover
    if nixos_startup_cursor_pending then
      local hyprcursor = hl.get_config("cursor.enable_hyprcursor")
      nixos_startup_cursor = {
        config = {
          invisible = hl.get_config("cursor.invisible"),
          enable_hyprcursor = hyprcursor,
          sync_gsettings_theme = hl.get_config("cursor.sync_gsettings_theme"),
        },
        hyprcursor = os.getenv("HYPRCURSOR_THEME"),
        size = tonumber((hyprcursor and os.getenv("HYPRCURSOR_SIZE")) or os.getenv("XCURSOR_SIZE")) or 24,
        path = normal_path(),
        xcursor = normal_theme(interrupted),
      }
      if nixos_startup_cursor.size <= 0 then nixos_startup_cursor.size = 24 end
      -- Compositor environment survives Lua reloads; a session id prevents stale inheritance.
      hl.env("NIXOS_STARTUP_CURSOR_THEME", nixos_startup_cursor.xcursor)
      hl.env("NIXOS_STARTUP_CURSOR_SESSION", os.getenv("HYPRLAND_INSTANCE_SIGNATURE"))
      if cold then
        hl.env("XCURSOR_PATH", os.getenv("NIXOS_PATH") .. "/default/hypr/cursors:" .. nixos_startup_cursor.path)
        hl.env("XCURSOR_THEME", "nixos-startup")
      else
        hl.env("XCURSOR_PATH", nixos_startup_cursor.path)
        hl.env("XCURSOR_THEME", nixos_startup_cursor.xcursor)
      end
    end
  end
  if nixos_startup_cursor_pending then
    -- Keep the temporary cursor private to the compositor, including GSettings.
    hl.config({ cursor = { invisible = true, enable_hyprcursor = false, sync_gsettings_theme = false } })
    hl.timer(function()
      if nixos_startup_cursor_pending then
        nixos_startup_cursor.restoring = false
        nixos_startup_cursor_restore()
      end
    end, { timeout = 15000, type = "oneshot" })
    if recover then nixos_startup_cursor_restore() end
  end
end)
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles"] = function(...)
local paths = require("default.hypr.paths")
local require_all = require("default.hypr.require_all")

local toggles_dir = paths.state_home .. "/nixos/toggles/hypr"
package.path = toggles_dir .. "/?.lua;" .. package.path

-- touchpad-disabled.lua / touchscreen-disabled.lua were generated Lua in older
-- versions and could carry an injected USB device name. They must never be loaded
-- as code again: exclude them so a not-yet-migrated install cannot execute a
-- leftover payload on reload. The migration recovers the name and deletes them.
require_all.files(toggles_dir, nil, {
  reload = true,
  exclude = {
    ["touchpad-disabled"] = true,
    ["touchscreen-disabled"] = true,
  },
})

local disabled_input_device = require("default.hypr.disabled-input-device")
disabled_input_device("touchpad")
disabled_input_device("touchscreen")

require("default.hypr.workspace-layouts")
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.bar-glassy
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.bar-glassy"] = function(...)
-- The Glassy bar: the shell draws the bar see-through, and Hyprland blurs what
-- is behind it.
require("default.hypr.glass")()

hl.layer_rule({
  match = { namespace = "^nixos-bar$" },
  blur = true,
  ignore_alpha = 0.3,
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.corners-rounded
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.corners-rounded"] = function(...)
-- Round window corners, whatever the theme sets. Matches Solitude's corners.
hl.config({
  decoration = {
    rounding = 6,
    rounding_power = 3,
  },
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.corners-sharp
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.corners-sharp"] = function(...)
-- Square window corners, whatever the theme sets.
hl.config({
  decoration = {
    rounding = 0,
  },
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.flags
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.flags"] = function(...)
-- This directory is intended for permanent config toggle flags.
-- Do not remove this file; the directory always needs at least one file.
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.no-animations
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.no-animations"] = function(...)
-- Draw nothing just for show, for machines that render on the CPU, like a VM:
-- no animations, blur or shadows. How see-through windows are is left to
-- Appearance > Windows > Window Opacity.
hl.config({
  animations = {
    enabled = false,
  },

  decoration = {
    blur = {
      enabled = false,
    },

    shadow = {
      enabled = false,
    },
  },
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.single-window-aspect-ratio
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.single-window-aspect-ratio"] = function(...)
-- Avoid overly wide single-window layouts on wide screens.
hl.config({
  layout = {
    single_window_aspect_ratio = { 1, 1 },
  },
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.window-glassy
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.window-glassy"] = function(...)
-- Frosted glass from the glassy Starship (#14726): whatever is behind a
-- see-through window or shell surface is blurred. Terminals get the see-through
-- background itself from nixos-theme-set-glass, which keeps their text crisp.
require("default.hypr.glass")()

-- GTK apps fade as a whole, since GTK draws their backgrounds solid, and get
-- their blur from the backdrop-filter Glassy adds to the user's gtk.css.
o.window("org\\.gnome\\.Nautilus", { opacity = "0.75 0.75" })

hl.layer_rule({
  match = { namespace = "^(nixos-bar|nixos-menu|nixos-menu-dim|nixos-notifications|nixos-osd|nixos-polkit|nixos-polkit-dim|nixos-reminders|nixos-clipboard|nixos-emojis|nixos-image-selector|nixos-keyboard-panel|nixos-network-qr)$" },
  blur = true,
  ignore_alpha = 0.3,
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.window-no-gaps
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.window-no-gaps"] = function(...)
-- Remove all window gaps and borders.
hl.config({
  general = {
    gaps_out = 0,
    gaps_in = 0,
    border_size = 0,
  },

  decoration = {
    rounding = 0,
  },
})
end

-- ----------------------------------------------------------------------------
-- default.hypr.toggles.window-opaque
-- ----------------------------------------------------------------------------
package.preload["default.hypr.toggles.window-opaque"] = function(...)
-- Opaque windows, even those NixOS makes transparent by default.
o.window({ tag = "transparent-window" }, { opacity = "1 1" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.windows
-- ----------------------------------------------------------------------------
package.preload["default.hypr.windows"] = function(...)
-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/

o.window(".*", { suppress_event = "maximize" })

-- Fix some dragging issues with XWayland.
o.window(
  {
    class = "^$",
    title = "^$",
    xwayland = true,
    float = true,
    fullscreen = false,
    pin = false,
  },
  { no_focus = true }
)

-- App-specific tweaks and terminal tags.
require("default.hypr.apps")

-- Terminals (including TUIs) and these desktop apps opt in to transparency.
o.transparent_window({ tag = "terminal" })
o.transparent_window("(omawrite|1[pP]assword|com\\.onepassword\\.OnePassword|org\\.gnome\\.Nautilus)")

-- The transparency hotkey opts otherwise opaque windows in with this tag.
o.transparent_window({ tag = "transparent" })
end

-- ----------------------------------------------------------------------------
-- default.hypr.workspace-layouts
-- ----------------------------------------------------------------------------
package.preload["default.hypr.workspace-layouts"] = function(...)
-- Restore workspace layouts saved by nixos-hyprland-workspace-layout-toggle.

local paths = require("default.hypr.paths")
local require_all = require("default.hypr.require_all")

-- The saved files call o.workspace_mode, so it has to exist before they load.
local workspace_modes = require("default.hypr.workspace-modes")

local layouts_dir = paths.state_home .. "/nixos/workspace-layouts"

-- The directory is found through XDG_STATE_HOME but the files are loaded by
-- module name, and bootstrap only puts ~/.local/state on the search path. A
-- state home anywhere else would list the saved layouts and then fail to require
-- them, or load same-named ones from under the home directory instead.
package.path = paths.state_home .. "/?.lua;" .. package.path

require_all.files(layouts_dir, "nixos.workspace-layouts", { reload = true })

-- With every saved mode known, bring the open windows in line and set up what a
-- floating workspace needs.
workspace_modes.apply()
end

-- ----------------------------------------------------------------------------
-- default.hypr.workspace-modes
-- ----------------------------------------------------------------------------
package.preload["default.hypr.workspace-modes"] = function(...)
-- Workspace modes for nixos-hyprland-workspace-layout-toggle.
--
-- Hyprland has dwindle and scrolling as tiled layouts, but nothing that floats a
-- whole workspace: it reports a workspace's `tiledLayout` and takes an unknown
-- layout name in silence, falling back to dwindle. So floating is applied to the
-- windows themselves.
--
-- Ending the mode has to tile the windows the mode floated and only those, so
-- each one is tagged. The tag lives on the window: it dies with it, follows it
-- between workspaces, and survives the config reload that a monitor being
-- plugged in performs, none of which a table on this side would do.
--
-- Every window on a floating workspace also carries a second tag, whether the
-- mode floated it or it was floating already. Titlebars, shadows, and full
-- opacity follow that tag, so a dialog on a floating workspace can be dragged by
-- its titlebar too, and a window carried out to a tiled one loses it.

require("default.hypr.helpers")
local paths = require("default.hypr.paths")

local FLOATED_TAG = "nixos-mode-floated"
local WORKSPACE_TAG = "nixos-floating-workspace"
local OPENED_TAG = "nixos-mode-opened"
local OPEN_RULE = "nixos-floating-open-"
local LAST_WORKSPACE = 2147483647
local TITLEBARS = "/usr/lib/nixos-hyprland-titlebars/titlebars.so"

local M = {}

local modes = {}
local default_mode = nil
local watching = false
-- Set up once per config load, on the first floating workspace.
local floating_ready = false
local set_up_floating
local cascade = 0
local open_rules = 0

local function set_floating(window, floating)
  hl.dispatch(hl.dsp.window.float({ action = floating and "on" or "off", window = window }))
end

local function set_claimed(window, claimed)
  hl.dispatch(hl.dsp.window.tag({ tag = (claimed and "+" or "-") .. FLOATED_TAG, window = window }))
end

local function set_on_floating_workspace(window, on)
  hl.dispatch(hl.dsp.window.tag({ tag = (on and "+" or "-") .. WORKSPACE_TAG, window = window }))
end

local function claimed()
  local addresses = {}

  for _, window in ipairs(hl.get_windows({ tag = FLOATED_TAG })) do
    addresses[window.address] = true
  end

  return addresses
end

-- Special workspaces, such as the scratchpad, and named ones, which report a
-- negative id, keep whatever state a window arrived with.
local function floating_workspace(id)
  id = tonumber(id)

  if not id or id < 1 then
    return false
  end

  local mode = modes[tostring(id)]
  if mode then
    return mode == "floating"
  end

  return default_mode == "floating"
end

local function anything_floats()
  if default_mode == "floating" then
    return true
  end

  for _, mode in pairs(modes) do
    if mode == "floating" then
      return true
    end
  end

  return false
end

-- A window the mode floats opens at a comfortable size in the middle of its
-- monitor, each one stepped from the last so a workspace floated all at once does
-- not leave every window stacked exactly on the one beneath it.
local function place(window)
  local monitor = window.monitor
  if not monitor or not monitor.width then
    return
  end

  local width = math.floor(monitor.width / monitor.scale)
  local height = math.floor(monitor.height / monitor.scale)

  if (monitor.transform or 0) % 2 == 1 then
    width, height = height, width
  end

  local reserved = monitor.reserved or {}
  width = width - (reserved.left or 0) - (reserved.right or 0)
  height = height - (reserved.top or 0) - (reserved.bottom or 0)

  hl.dispatch(hl.dsp.window.resize({
    x = math.min(1100, math.floor(width * 0.64)),
    y = math.min(760, math.floor(height * 0.68)),
    relative = false,
    window = window,
  }))
  hl.dispatch(hl.dsp.window.center({ window = window }))

  cascade = (cascade + 1) % 5
  hl.dispatch(hl.dsp.window.move({ x = cascade * 24 - 48, y = cascade * 24 - 48, relative = true, window = window }))
end

-- A window already floating on its own account -- an app with a float rule of
-- its own, a dialog, one popped out with SUPER + T -- is left unclaimed, so it
-- is still floating when the mode ends. A fullscreen window is left as it is.
--
-- Every tiled window is claimed before any of them is floated: floating one
-- member of a group floats the rest, and a single pass would then find those
-- already floating and leave them to be stranded when the mode ends.
local function float_for_mode(windows)
  local claiming = {}

  for _, window in ipairs(windows) do
    set_on_floating_workspace(window, true)

    if not window.floating and (window.fullscreen or 0) == 0 then
      set_claimed(window, true)
      table.insert(claiming, window)
    end
  end

  for _, window in ipairs(claiming) do
    set_floating(window, true)
    place(window)
  end
end

-- A pinned window is one the user asked to keep above everything, and tiling it
-- would unpin it as well, so the mode leaves it be.
local function tile_for_mode(window, mine)
  set_on_floating_workspace(window, false)

  if not mine[window.address] or window.pinned then
    return
  end

  set_claimed(window, false)
  set_floating(window, false)
end

-- The floating workspaces as ranges of ids, for window rules to match.
local function floating_ranges()
  local ranges = {}

  if default_mode == "floating" then
    local tiled = {}
    for id, mode in pairs(modes) do
      local n = tonumber(id)
      if n and n >= 1 and mode ~= "floating" then
        table.insert(tiled, n)
      end
    end
    table.sort(tiled)

    local from = 1
    for _, n in ipairs(tiled) do
      if n > from then
        table.insert(ranges, { from, n - 1 })
      end
      from = n + 1
    end
    table.insert(ranges, { from, LAST_WORKSPACE })
  else
    for id, mode in pairs(modes) do
      local n = tonumber(id)
      if n and n >= 1 and mode == "floating" then
        table.insert(ranges, { n, n })
      end
    end
    table.sort(ranges, function(a, b) return a[1] < b[1] end)
  end

  return ranges
end

-- The size the mode gives a window, and where it opens: centered, and stepped
-- from the last one so windows opened one after another do not stack exactly
-- on each other. The window's own size is not settled when the rule places it,
-- so the position is worked out from the size the rule gives it.
local OPEN_WIDTH = "min(1100,monitor_w*0.64)"
local OPEN_HEIGHT = "min(760,monitor_h*0.68)"

local function open_position()
  local step = cascade * 24 - 48
  return string.format("(monitor_w-%s)/2+(%d) (monitor_h-%s)/2+(%d)", OPEN_WIDTH, step, OPEN_HEIGHT, step)
end

-- Matches every window but those of apps with float rules of their own,
-- directly or through a tag a float rule matches.
local function not_floating_on_their_own(match)
  local floating = o.floating_apps or { class = {}, title = {}, tags = {}, tagged = {} }
  local excluded = { class = {}, title = {} }
  for _, key in ipairs({ "class", "title" }) do
    for _, pattern in ipairs(floating[key]) do
      table.insert(excluded[key], pattern)
    end
  end
  for tag in pairs(floating.tags) do
    for _, tagged in ipairs(floating.tagged[tag] or {}) do
      table.insert(excluded[tagged.key], tagged.pattern)
    end
  end

  for _, key in ipairs({ "class", "title" }) do
    local patterns = excluded[key]
    if #patterns > 0 then
      local alternatives = {}
      for _, pattern in ipairs(patterns) do
        table.insert(alternatives, "(?:" .. pattern .. ")")
      end
      match[key] = "negative:" .. table.concat(alternatives, "|")
    end
  end
  return match
end

-- A window opening on a floating workspace floats from its first frame, at the
-- size the mode gives it, so it pops in from its own middle the way a tiled
-- window does, instead of opening tiled and shrinking into place. Modal
-- dialogs, and apps with float rules of their own, float on their own account
-- and are left to it, at their own size and outside the mode's claim.
local function sync_open_rules()
  local ranges = floating_ranges()

  for i, range in ipairs(ranges) do
    hl.window_rule({
      name = OPEN_RULE .. i,
      enabled = true,
      match = not_floating_on_their_own({ workspace = string.format("r[%d-%d]", range[1], range[2]), modal = false }),
      float = true,
      size = OPEN_WIDTH .. " " .. OPEN_HEIGHT,
      move = open_position(),
      tag = "+" .. OPENED_TAG,
    })
  end

  for i = #ranges + 1, open_rules do
    hl.window_rule({ name = OPEN_RULE .. i, enabled = false })
  end

  open_rules = math.max(open_rules, #ranges)
end

-- Personal rules can follow saved workspace modes in hyprland.lua. Keep the
-- exclusions current before their first window opens, including tag rules.
o.floating_apps_changed = sync_open_rules

-- A rule's tag leaves with the rule, so a window the open rule floated is
-- claimed for good as it opens, and the mode tiles it again when it ends. A
-- rule's tags are listed with a trailing "*", and a strict tag query passes
-- them over, so the window's own list is read.
local function claim_opened(window)
  for _, tag in ipairs(window.tags or {}) do
    if tag == OPENED_TAG or tag == OPENED_TAG .. "*" then
      set_claimed(window, true)
      -- The next window the rule opens steps on from this one.
      cascade = (cascade + 1) % 5
      sync_open_rules()
      return
    end
  end
end

-- A maximized window has a floating workspace to itself until another one
-- opens there, which brings it back to its own size so the two can share it.
local function unmaximize_others(window)
  local id = window.workspace and window.workspace.id
  if not floating_workspace(id) then
    return
  end

  for _, other in ipairs(hl.get_workspace_windows(tostring(id))) do
    if other.address ~= window.address and (other.fullscreen or 0) == 1 then
      hl.dispatch(hl.dsp.window.fullscreen({ mode = "maximized", action = "unset", window = other }))
    end
  end
end

-- The workspace is passed in when a window is still on its way to it.
local function arrange(windows, workspace)
  local floating = {}
  local mine = claimed()

  for _, window in ipairs(windows) do
    local id = tonumber(workspace and workspace.id or (window.workspace and window.workspace.id))

    if id and id >= 1 then
      if floating_workspace(id) then
        table.insert(floating, window)
      else
        tile_for_mode(window, mine)
      end
    end
  end

  float_for_mode(floating)
end

-- Overlapping windows are placed with the pointer, so a floating workspace
-- focuses on click rather than on hover. Every other workspace keeps the user's
-- own setting.
local input = {}

local function update_input()
  local workspace = hl.get_active_workspace()
  local active = workspace ~= nil and floating_workspace(workspace.id)

  if active == input.floating then
    return
  end

  input.floating = active

  hl.config({ input = { follow_mouse = active and 0 or input.follow_mouse } })
end

-- Windows arrive by opening and by being carried in, and a window rule only ever
-- fires for the first. One carried back out gives up the floating the mode gave
-- it rather than staying floating somewhere that tiles.
local function watch()
  if watching then
    return
  end

  watching = true

  input.follow_mouse = hl.get_config("input.follow_mouse")

  hl.on("window.open", function(window)
    claim_opened(window)
    unmaximize_others(window)
    arrange({ window })
  end)

  -- A move is still being committed when this fires, and changing the window's
  -- floating state underneath it loses the move. Let it land first.
  hl.on("window.move_to_workspace", function(window, workspace)
    hl.timer(function()
      arrange({ window }, workspace)
    end, { type = "oneshot", timeout = 1 })
  end)

  -- A fullscreen window is left as it is, so it is arranged once it comes back
  -- out: a tiled one leaving fullscreen on a floating workspace floats then.
  hl.on("window.fullscreen", function(window)
    hl.timer(function()
      arrange({ window })
    end, { type = "oneshot", timeout = 1 })
  end)

  hl.on("workspace.active", update_input)
  hl.on("monitor.focused", update_input)
end

function o.workspace_mode(spec)
  watch()

  -- The default for every workspace that has no mode of its own, chosen under
  -- Appearance > Workspace Layout. A tiled default is Hyprland's own
  -- layout; a floating one is arranged once the saved modes have all loaded.
  if spec.default then
    default_mode = spec.default
    if spec.default ~= "floating" then
      hl.config({ general = { layout = spec.default } })
    end
    sync_open_rules()
    if anything_floats() then
      set_up_floating()
    end
    return
  end

  local workspace = tostring(spec.workspace)

  -- Floating keeps whatever tiled layout the workspace had, so nothing has to be
  -- chosen for it on the way back out.
  if spec.mode ~= "floating" then
    hl.workspace_rule({ workspace = workspace, layout = spec.mode })
  end

  modes[workspace] = spec.mode

  if anything_floats() then
    set_up_floating()
  end

  arrange(hl.get_workspace_windows(workspace))
  sync_open_rules()
  update_input()
end

local function theme_colors()
  local colors = {}
  -- nixos-theme-set writes the current theme under ~/.local/state whatever
  -- XDG_STATE_HOME says, and Hyprland loads the theme's own config from there.
  local file = io.open(paths.home .. "/.local/state/nixos/current/theme/colors.toml", "r")

  if file then
    for line in file:lines() do
      local key, value = line:match('^%s*([%w_]+)%s*=%s*"#(%x%x%x%x%x%x)"')
      if key then
        colors[key] = "rgb(" .. value .. ")"
      end
    end

    file:close()
  end

  local background = colors.background or "rgb(1a1b26)"
  -- A titlebar in the window's own background color runs into the window, so it
  -- takes the theme's raised surface. Themes that make that the background too
  -- fall back to their selection color.
  local titlebar = colors.lighter_background
  if not titlebar or titlebar == background then
    titlebar = colors.selection or background
  end

  return {
    background = background,
    foreground = colors.foreground or "rgb(c0caf5)",
    titlebar = titlebar,
  }
end

-- Titlebars come from nixos-hyprland-titlebars, loaded once something floats.
-- The plugin reloads the config once it is in, which is the pass that finds its
-- options here. Its options reset on every load, so it draws nothing until enabled.
local function titlebars_installed()
  local file = io.open(TITLEBARS, "r")
  if not file then
    return false
  end
  file:close()
  return true
end

local function titlebars()
  if not titlebars_installed() then
    return
  end

  hl.plugin.load(TITLEBARS)

  if not hl.plugin.hyprbars then
    return
  end

  local colors = theme_colors()
  local window = [[window = "address:%WINDOW%"]]

  hl.config({
    plugin = {
      hyprbars = {
        enabled = true,
        workspace_tag = WORKSPACE_TAG,
        bar_height = 30,
        bar_color = colors.titlebar,
        col = { text = colors.foreground },
        bar_text_font = "monospace",
        bar_text_size = 12,
        bar_text_weight = "normal",
        bar_text_align = "left",
        bar_buttons_alignment = "right",
        bar_part_of_window = true,
        bar_precedence_over_border = true,
        bar_padding = 10,
        bar_button_padding = 8,
        button_rounding = 0,
        icon_on_hover = false,
        inactive_button_color = colors.titlebar,
        on_double_click = "hyprctl dispatch 'hl.dsp.window.fullscreen({ mode = \"maximized\", action = \"toggle\", " .. window .. " })'",
      },
    },
  })

  for _, button in ipairs({
    { icon = "×", action = "hyprctl dispatch 'hl.dsp.window.close({ " .. window .. " })'" },
    { icon = "□", action = "hyprctl dispatch 'hl.dsp.window.fullscreen({ mode = \"maximized\", action = \"toggle\", " .. window .. " })'" },
    -- Minimized windows wait in the dock, which brings them back.
    { icon = "−", action = "nixos-hyprland-window-minimize %WINDOW%" },
  }) do
    hl.plugin.hyprbars.add_button({
      bg_color = colors.titlebar,
      fg_color = colors.foreground,
      size = 20,
      icon = button.icon,
      action = button.action,
    })
  end
end

-- Hyprland unloads a plugin the config stops asking for, and bringing this one
-- back costs a cascade of reloads, so once in it stays asked for all session.
local function titlebars_loaded()
  for _, plugin in ipairs(hl.get_loaded_plugins and hl.get_loaded_plugins() or {}) do
    if plugin.name == "hyprbars" then
      return true
    end
  end

  return false
end

-- Runs once every saved mode has loaded. A reload is a fresh start on this side
-- but not for the windows, so each one is brought in line with the modes as they
-- now stand: moving the default away from floating has to give back what it
-- floated, even though nothing names those workspaces any more.
function M.apply()
  -- A default that no longer floats can leave no saved mode at all to start the
  -- watchers, while the windows it floated still carry its tags.
  local leftovers = #hl.get_windows({ tag = FLOATED_TAG }) > 0 or #hl.get_windows({ tag = WORKSPACE_TAG }) > 0

  if anything_floats() or leftovers then
    watch()
  end

  if watching then
    arrange(hl.get_windows())
    update_input()
  end

  if anything_floats() then
    set_up_floating()
  elseif titlebars_loaded() and titlebars_installed() then
    hl.plugin.load(TITLEBARS)
  end
end

-- What floating workspaces need on top of the rest of the config: shadows,
-- opaque windows, and titlebars. Run while the config loads when something
-- floats already, and otherwise the moment a workspace starts floating, so
-- Super + L brings titlebars without reloading Hyprland.
set_up_floating = function()
  if floating_ready then
    return
  end
  floating_ready = true

  -- Overlapping windows need depth to tell apart, and a translucent window over
  -- another is hard to read.
  if not hl.get_config("decoration.shadow.enabled") then
    hl.config({ decoration = { shadow = { enabled = true, range = 16, render_power = 3, color = "rgba(00000035)" } } })
    o.window(".*", { no_shadow = true })
    o.window({ tag = WORKSPACE_TAG }, { no_shadow = false })
  end

  o.window({ tag = WORKSPACE_TAG }, { opacity = "1.0 override 1.0 override" })

  titlebars()
end

return M
end

-- ============================================================================
-- 3. Personal modules
-- ============================================================================
-- ----------------------------------------------------------------------------
-- hypr.appearance
-- ----------------------------------------------------------------------------
package.preload["hypr.appearance"] = function(...)
-- Window appearance module for the "Rounded Corner Blur" bar-widget plugin.
--
-- Place this file at ~/.config/hypr/appearance.lua and add
--   require ("hypr.appearance")
-- near the top of ~/.config/hypr/hyprland.lua (after `require ("hypr.looknfeel")`
-- if present). The plugin writes appearance state to
-- ~/.local/state/nixos/appearance.lua and triggers `hyprctl reload`. This
-- module is loaded on every Hyprland config reload and applies that state via
-- hl.config(). When the state file is missing (fresh install, or after Reset),
-- this module is a no-op and the NixOS defaults / active theme win.

local home = os.getenv("HOME")
local state_file = home and (home .. "/.local/state/nixos/appearance.lua") or nil

local function load_state()
  if not state_file then
    return nil
  end

  local file = io.open(state_file, "r")
  if not file then
    return nil
  end

  local chunk = file:read("*a")
  file:close()

  if not chunk then
    return nil
  end

  local ok, state = pcall(load, chunk)
  if not ok or type(state) ~= "function" then
    return nil
  end

  local ok2, result = pcall(state)
  if not ok2 or type(result) ~= "table" then
    return nil
  end

  return result
end

local function blur_enabled(state)
  local blur = state.blur
  if type(blur) ~= "table" then
    return false
  end
  return blur.enabled == true
end

local state = load_state()
if state then
  local decoration = {}

  if state.rounding ~= nil then
    decoration.rounding = math.floor(state.rounding + 0.5)
  end

  if state.active_opacity ~= nil
    and state.active_opacity >= 0
    and state.active_opacity <= 1 then
    decoration.active_opacity = state.active_opacity
  end

  if state.inactive_opacity ~= nil
    and state.inactive_opacity >= 0
    and state.inactive_opacity <= 1 then
    decoration.inactive_opacity = state.inactive_opacity
  end

  local blur = state.blur
  if type(blur) == "table" then
    decoration.blur = { enabled = blur_enabled(state) }
    if blur_enabled(state) then
      if blur.size ~= nil then
        decoration.blur.size = math.floor(blur.size + 0.5)
      end
      if blur.passes ~= nil then
        decoration.blur.passes = math.floor(blur.passes + 0.5)
      end
    end
  end

  hl.config({ decoration = decoration })
end
end

-- ----------------------------------------------------------------------------
-- hypr.autostart
-- ----------------------------------------------------------------------------
package.preload["hypr.autostart"] = function(...)
-- Extra autostart processes.
-- o.launch_on_start("my-service")

-- Spotify и Discord на втором мониторе (HDMI-A-4, воркспейс 5)
o.exec_on_start("~/.config/hypr/scripts/autostart-media.sh")

-- Deadlock: через 2 минуты после входа заранее положить карты/шейдеры/паки в оперативку
-- (низкий приоритет, фоновые ядра), чтобы к запуску игры ничего не читалось с диска.
o.exec_on_start("~/.local/bin/deadlock-preload warm 120")
end

-- ----------------------------------------------------------------------------
-- hypr.bindings
-- ----------------------------------------------------------------------------
package.preload["hypr.bindings"] = function(...)
-- ==========================================
-- 0. ДОБАВЛЕНО 25.11: чего не было в своих биндах (база выключена: nixos_default_bindings = false в разделе 4)
-- ==========================================
-- журнал буфера обмена на Win+V, как в Windows (панель nixos.clipboard, cliphist)
o.bind("SUPER + V", "Clipboard history", { panel = "nixos.clipboard" })
-- кнопка питания — сразу выключить компьютер
o.bind("XF86PowerOff", "Power off", "systemctl poweroff", { locked = true })
-- крышка ноутбука
o.bind("switch:on:Lid Switch", nil, "nixos-system-lid-close", { locked = true })
o.bind("switch:off:Lid Switch", nil, "nixos-hyprland-monitor-clamshell", { locked = true })
o.bind("switch:on:Apple SMC power/lid events", nil, "nixos-system-lid-close", { locked = true })
o.bind("switch:off:Apple SMC power/lid events", nil, "nixos-hyprland-monitor-clamshell", { locked = true })
-- медиаклавиши (громкость — своя, раздел 2): плей/пауза/треки, яркость, микрофон, подсветка, тачпад
o.bind("XF86AudioMicMute", "Mute microphone", "nixos-audio-input-mute", { locked = true })
o.bind("XF86MonBrightnessUp", "Brightness up", { brightness = "raise" }, { locked = true, repeating = true })
o.bind("XF86MonBrightnessDown", "Brightness down", { brightness = "lower" }, { locked = true, repeating = true })
o.bind("SHIFT + XF86MonBrightnessUp", "Brightness maximum", "nixos-brightness-display 100%", { locked = true, repeating = true })
o.bind("SHIFT + XF86MonBrightnessDown", "Brightness minimum", "nixos-brightness-display 1%", { locked = true, repeating = true })
o.bind("XF86KbdBrightnessUp", "Keyboard brightness up", "nixos-brightness-keyboard up", { locked = true, repeating = true })
o.bind("XF86KbdBrightnessDown", "Keyboard brightness down", "nixos-brightness-keyboard down", { locked = true, repeating = true })
o.bind("CTRL + XF86MonBrightnessDown", "Keyboard brightness down", "nixos-brightness-keyboard down", { locked = true, repeating = true })
o.bind("CTRL + XF86MonBrightnessUp", "Keyboard brightness up", "nixos-brightness-keyboard up", { locked = true, repeating = true })
o.bind("XF86KbdLightOnOff", "Keyboard backlight cycle", "nixos-brightness-keyboard cycle", { locked = true })
o.bind_toggle("XF86TouchpadToggle", "Toggle touchpad", "touchpad", { locked = true })
o.bind("XF86TouchpadOn", "Enable touchpad", "nixos-toggle-touchpad on", { locked = true })
o.bind("XF86TouchpadOff", "Disable touchpad", "nixos-toggle-touchpad off", { locked = true })
o.bind("ALT + XF86AudioRaiseVolume", "Volume up precise", "nixos-audio-output-volume +1", { locked = true, repeating = true })
o.bind("ALT + XF86AudioLowerVolume", "Volume down precise", "nixos-audio-output-volume -1", { locked = true, repeating = true })
o.bind("ALT + XF86MonBrightnessUp", "Brightness up precise", "nixos-brightness-display +1%", { locked = true, repeating = true })
o.bind("ALT + XF86MonBrightnessDown", "Brightness down precise", "nixos-brightness-display 1%-", { locked = true, repeating = true })
o.bind("XF86AudioNext", "Next track", { ipc = "media.next" }, { locked = true })
o.bind("ALT + XF86AudioPlay", "Next track", { ipc = "media.next" }, { locked = true })
o.bind("XF86AudioPause", "Pause", { ipc = "media.playPause" }, { locked = true })
o.bind("XF86AudioPlay", "Play", { ipc = "media.playPause" }, { locked = true })
o.bind("XF86AudioPrev", "Previous track", { ipc = "media.previous" }, { locked = true })
o.bind("ALT + SHIFT + XF86AudioPlay", "Previous track", { ipc = "media.previous" }, { locked = true })
o.bind("XF86Eject", "Eject media", "eject", { locked = true })
o.bind("SHIFT + XF86AudioMute", "Switch audio output", "nixos-audio-output-switch", { locked = true })
o.bind("SHIFT + XF86AudioPause", "Switch media source", "nixos-audio-source-switch", { locked = true })
o.bind("SHIFT + XF86AudioPlay", "Switch media source", "nixos-audio-source-switch", { locked = true })

-- ==========================================
-- 1. ТВОИ КАСТОМНЫЕ БИНДЫ (ПРОГРАММЫ И МЕНЮ)
-- ==========================================

-- Меню NixOS (Win+Alt+B — список программ — убран 24.11 по просьбе)
o.bind("SUPER + B", "NixOS Menu", "nixos-menu toggle root")

-- Launch the default terminal (currently Ghostty) and Firefox
-- Терминал сразу (24.11): новое окно у фонового Ghostty (app-com.mitchellh.ghostty.service)
-- по D-Bus — ~50 мс вместо ~120 мс через xdg-terminal-exec → ghostty-fast → ghostty +new-window.
-- Если фонового Ghostty нет — прежний путь.
o.bind("SUPER + T", "Terminal",
  "gdbus call --session --dest com.mitchellh.ghostty --object-path /com/mitchellh/ghostty"
  .. " --method org.gtk.Actions.Activate new-window [] {} >/dev/null 2>&1 || xdg-terminal-exec")
-- и без анимации появления (popin ~0,4 с): окно терминала показывается сразу готовым
hl.window_rule({ name = "terminal-instant", match = { class = "^com\\.mitchellh\\.ghostty$" }, no_anim = true })
o.bind("SUPER + R", "Browser", "firefox")

-- Открепление и закрепление окон в тайлинге (Toggle Floating) — бинд SUPER + RETURN ниже, в разделе 3

-- ==========================================
-- 2. МУЛЬТИМЕДИА И СКРИНШОТЫ
-- ==========================================

-- Управление звуком (громкость +/- и выключение звука)
o.bind("XF86AudioRaiseVolume", "Volume Up", "wpctl set-volume -l 1.5 @DEFAULT_AUDIO_SINK@ 5%+")
o.bind("XF86AudioLowerVolume", "Volume Down", "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-")
o.bind("XF86AudioMute", "Mute Audio", "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")

-- Скриншот области экрана на SUPER + SHIFT + S (сразу копирует в буфер обмена)
o.bind("SUPER + SHIFT + S", "Screenshot Area", "grim -g \"$(slurp)\" - | wl-copy")

-- ==========================================
-- 3. БАЗОВОЕ УПРАВЛЕНИЕ СИСТЕМОЙ
-- =========================================

o.bind("SUPER + RETURN", "Toggle Floating", hl.dsp.window.float({ action = "toggle" }))

-- SUPER + P (сквозное закрепление плавающих окон) — в pin-ghost.lua

-- Fenster mit Super + Linksklick verschieben
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })

-- Fenster mit Super + Rechtsklick vergrößern/verkleinern
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Закрытие активного окна на Super + Q
hl.bind("SUPER + Q", hl.dsp.window.close())

-- Firefox на Wayland берёт размер экрана с первого монитора (1920x1080). Если окно уже
-- развёрнуто через SUPER+F, а потом включить фуллскрин видео, на HDMI-A-4 (1920x1280) видео
-- рисовалось 1920x1080 с серой полосой снизу. Поэтому браузеру не сообщаем о фуллскрине
-- Hyprland (client = 0) — тогда фуллскрин видео получает от Hyprland реальный размер.
local function is_firefox(window)
  for _, tag in ipairs(window.tags or {}) do
    if tag:gsub("%*$", "") == "firefox-based-browser" then
      return true
    end
  end
  return false
end

hl.bind("SUPER + F", function()
  local window = hl.get_active_window()
  if window and is_firefox(window) and (window.fullscreen or 0) == 0 then
    hl.dispatch(hl.dsp.window.fullscreen_state({ internal = 2, client = 0 }))
  else
    hl.dispatch(hl.dsp.window.fullscreen({ action = "toggle" }))
  end
end)

-- Привязка воркспейсов к мониторам (Workspace Rules)
hl.workspace_rule({ workspace = "1", monitor = "HDMI-A-3", persistent = true })
hl.workspace_rule({ workspace = "2", monitor = "HDMI-A-3", persistent = true })
hl.workspace_rule({ workspace = "3", monitor = "HDMI-A-3", persistent = true })
hl.workspace_rule({ workspace = "4", monitor = "HDMI-A-3", persistent = true })
hl.workspace_rule({ workspace = "5", monitor = "HDMI-A-4", persistent = true })

-- Бинд на переключение фокуса (Super + Цифра)
-- Super+1..4 — в workspace-switch.lua (без анимации при уходе с fullscreen)
hl.bind("SUPER + 5", hl.dsp.focus({ workspace = "5" }))

-- Бинд на перемещение окон (Super + Shift + Цифра)
hl.bind("SUPER + SHIFT + 1", hl.dsp.window.move({ workspace = "1" }))
hl.bind("SUPER + SHIFT + 2", hl.dsp.window.move({ workspace = "2" }))
hl.bind("SUPER + SHIFT + 3", hl.dsp.window.move({ workspace = "3" }))
hl.bind("SUPER + SHIFT + 4", hl.dsp.window.move({ workspace = "4" }))
hl.bind("SUPER + SHIFT + 5", hl.dsp.window.move({ workspace = "5" }))

-- SUPER + SHIFT + F (Spotify <-> Discord) — в media-toggle.lua

-- Ctrl+Shift+Esc: диспетчер задач (btop), повторное нажатие фокусирует уже открытый
o.bind("CTRL + SHIFT + ESCAPE", "Activity", { tui = "btop", focus = true })

-- Dictation keys from before Alt + Space and Right Alt became the defaults.
-- Remove these lines to give the keys back to applications.
if o.dictation_installed and o.dictation_installed() then
  o.bind("SUPER + CTRL + X", "Toggle dictation", "nixos-dictation toggle")
  o.bind_hold("F9", "Start dictation (push-to-talk)", "nixos-dictation start", "Stop dictation (push-to-talk)", "nixos-dictation stop")
end
end

-- ----------------------------------------------------------------------------
-- hypr.deadlock
-- ----------------------------------------------------------------------------
package.preload["hypr.deadlock"] = function(...)
-- Deadlock: настоящий полный экран (direct scanout) + tearing, всегда на 144-Гц мониторе.
-- Класс окна: steam_app_1422450 (Xwayland), deadlock(.exe) (Proton Wayland),
-- gamescope (режим суперсэмплинга из ~/.local/bin/deadlock-launch).
-- Tearing работает, только когда игра в полном экране и одна на мониторе
-- (проверка: hyprctl monitors → tearingBlockedBy).
hl.config({ general = { allow_tearing = true } })

local game = {
  immediate = true,
  fullscreen = true,
  monitor = "HDMI-A-3",
  idle_inhibit = "fullscreen",
}

o.window("^(steam_app_1422450|[Dd]eadlock(\\.exe)?)$", game)
o.window("^gamescope$", game)
end

-- ----------------------------------------------------------------------------
-- hypr.input
-- ----------------------------------------------------------------------------
package.preload["hypr.input"] = function(...)
hl.config({
  input = {
    kb_layout = (function() local f = io.open("/etc/nixos-share/keyboard"); if not f then return "us,ru" end; local s = f:read("l"); f:close(); return s end)(),
    kb_options = "grp:win_space_toggle",
    repeat_rate = 25,
    follow_mouse = 1,
    repeat_delay = 250,
    accel_profile = "flat", -- 1:1 без ускорения, как в win10 VM (MarkC fix)
    sensitivity = 0.2,
  }
})

-- Мышь отдельно для каждого монитора, переключается, когда курсор переходит на другой монитор.
-- default: 1:1 без ускорения как в win10 VM, чуть быстрее (множитель 1.2).
-- HDMI-A-4: adaptive-ускорение libinput, чуть медленнее стандартного.
local MOUSE = {
  default = { accel_profile = "flat", sensitivity = 0.2 },
  ["HDMI-A-4"] = { accel_profile = "adaptive", sensitivity = -0.15 },
}

hl.on("monitor.focused", function(mon)
  hl.config({ input = (mon and MOUSE[mon.name]) or MOUSE.default })
end)

-- Область монитора задаётся здесь, а в OTD Display = весь диапазон устройства (1920x1720).
end

-- ----------------------------------------------------------------------------
-- hypr.looknfeel
-- ----------------------------------------------------------------------------
package.preload["hypr.looknfeel"] = function(...)
-- Change the default NixOS look'n'feel.

-- https://wiki.hypr.land/Configuring/Basics/Variables/#general
-- hl.config({
--   general = {
--     -- No gaps between windows or borders.
--     gaps_in = 0,
--     gaps_out = 0,
--     border_size = 0,
--
--     -- Change to niri-like side-scrolling layout.
--     layout = "scrolling",
--   },
-- })

-- https://wiki.hypr.land/Configuring/Basics/Variables/#decoration
-- hl.config({
--   decoration = {
--     -- Use round window corners.
--     rounding = 8,
--
--     -- Dim unfocused windows (0.0 = no dim, 1.0 = fully dimmed).
--     dim_inactive = true,
--     dim_strength = 0.15,
--   },
-- })

-- https://wiki.hypr.land/Configuring/Basics/Variables/#animations
-- hl.config({
--   animations = {
--     -- Disable all animations.
--     enabled = false,
--   },
-- })

-- https://wiki.hypr.land/Configuring/Basics/Variables/#layout
-- hl.config({
--   layout = {
--     -- Avoid overly wide single-window layouts on wide screens.
--     single_window_aspect_ratio = { 1, 1 },
--   },
-- })

-- https://wiki.hypr.land/Configuring/Layouts/Scrolling-Layout/
-- hl.config({
--   scrolling = {
--     -- See only one column per screen instead of two.
--     column_width = 0.97,
--   },
-- })

-- Курсоры Material Design Dark (сконвертированы из Windows-пака ~/Projects/material_design_cursors_dark).
hl.env("XCURSOR_THEME", "material-design-dark")
hl.env("XCURSOR_SIZE", "26")
hl.env("HYPRCURSOR_SIZE", "26")
-- Та же тема в формате hyprcursor (hyprcursors/ + manifest.hl рядом с cursors/):
-- Hyprland рисует курсор сам и иначе берёт стандартную стрелку.
hl.env("HYPRCURSOR_THEME", "material-design-dark")

-- Обводка активного окна в лавандовом цвете бара (Catppuccin Mocha #b4befe),
-- поверх цвета темы.
hl.config({
  general = {
    col = {
      active_border = "rgb(b4befe)",
    },
  },
  group = {
    col = {
      border_active = "rgb(b4befe)",
    },
  },
})

-- Анимация переключения воркспейсов — в workspace-switch.lua.

-- Direct scanout: полноэкранная игра выводится на монитор в обход композитора
-- (меньше задержка и нагрузка). 2 = только для окон с content-type "game".
hl.config({
  render = {
    direct_scanout = 2,
  },
})

-- Opt another application in to NixOS's standard transparency.
-- Find its class with: hyprctl clients
-- o.transparent_window("my-app")
-- o.transparent_window("my-app", "0.9 0.85") -- Custom active/inactive opacity.
end

-- ----------------------------------------------------------------------------
-- media-toggle
-- ----------------------------------------------------------------------------
package.preload["media-toggle"] = function(...)
-- Win+Shift+F: на втором мониторе переключает Spotify <-> Discord/Vesktop на весь экран.
-- Оба окна остаются на workspace 5 с одинаковым размером.
-- Переключается полноэкранный слой композитора, без fullscreen-событий клиентам.
 
local MON         = "HDMI-A-4"      -- второй монитор
local WS          = "5"
local SPOTIFY_CMD = "spotify"
local DISCORD_CMD = "discord"       -- или "discord"
 
-- Без переходов при переносе/разворачивании: анимация показывала промежуточный
-- размер окна и создавала ощущение задержки даже при готовом приложении.
hl.window_rule({
    name = "media-toggle-instant",
    match = { class = "^(spotify|Spotify|discord|Discord|vesktop|Vesktop)$" },
    no_anim = true,
    sync_fullscreen = false,
    border_size = 0,
    rounding = 0,
    no_shadow = true,
})

local prepared = {}
local shown

local function main_windows()
    local spot, disc
    -- Один снимок окон. Не выбираем updater/диалог вместо основного окна.
    local function score(w)
        local size = w.size or {}
        return (size.x or size[1] or 0) * (size.y or size[2] or 0)
    end
    for _, w in ipairs(hl.get_windows()) do
        local c = (w.class or ""):lower()
        local title = (w.title or ""):lower()
        if not title:find("updater", 1, true) and w.mapped ~= false then
            if c == "spotify" and (not spot or score(w) > score(spot)) then
                spot = w
            elseif (c == "discord" or c == "vesktop") and (not disc or score(w) > score(disc)) then
                disc = w
            end
        end
    end
    return spot, disc
end
 
hl.bind("SUPER + SHIFT + F", function()
    local mon = hl.get_monitor(MON)
    if not mon or not mon.active_workspace then return end
 
    local spot, disc = main_windows()
 
    -- если что-то не запущено — запускаем
    if not spot then hl.exec_cmd(SPOTIFY_CMD) return end
    if not disc then hl.exec_cmd(DISCORD_CMD) return end
 
    local previous = hl.get_active_window()
    local workspace = hl.get_workspace(WS)
    local current = workspace and workspace.fullscreen_window
    if mon.active_workspace.id ~= tonumber(WS) then
        if disc.workspace and disc.workspace.id == mon.active_workspace.id then current = disc
        elseif spot.workspace and spot.workspace.id == mon.active_workspace.id then current = spot end
    end
    if not current or (current.address ~= spot.address and current.address ~= disc.address) then
        -- При обновлении старой версии Discord может ещё быть на media-discord.
        if disc.workspace and disc.workspace.id == mon.active_workspace.id then
            current = disc
        elseif shown == disc.address then
            current = disc
        else
            current = spot
        end
    end
    local target = current.address == spot.address and disc or spot
    local target_sel = "address:" .. target.address

    local width = math.floor(mon.width / mon.scale)
    local height = math.floor(mon.height / mon.scale)
    if (mon.transform or 0) % 2 == 1 then width, height = height, width end
    local geometry = table.concat({ mon.x, mon.y, width, height, mon.scale }, ":")
    local function fullscreen(w, internal)
        hl.dispatch(hl.dsp.window.fullscreen_state({
            window = "address:" .. w.address, internal = internal, client = 0, action = "set",
        }))
    end

    -- Сохраняем плавающий размер равным полноэкранному. При снятии внутреннего
    -- fullscreen Hyprland восстановит тот же размер, а не маленькое tiled-окно.
    local function prepare(w)
        local placed = w.workspace and w.workspace.id == tonumber(WS)
        if placed and w.floating and prepared[w.address] == geometry then return end
        local sel = "address:" .. w.address
        fullscreen(w, 0)
        if not placed then
            hl.dispatch(hl.dsp.window.move({ workspace = WS, window = sel, follow = false }))
        end
        if not w.floating then
            hl.dispatch(hl.dsp.window.float({ window = sel, action = "set" }))
        end
        hl.dispatch(hl.dsp.window.resize({ window = sel, x = width, y = height, relative = false }))
        hl.dispatch(hl.dsp.window.move({ window = sel, x = mon.x, y = mon.y, relative = false }))
    end
    prepare(spot)
    prepare(disc)
    prepared = { [spot.address] = geometry, [disc.address] = geometry }

    if current.fullscreen ~= 0 then fullscreen(current, 0) end
    fullscreen(target, 2)
    shown = target.address

    workspace = hl.get_workspace(WS)
    if not workspace then return end
    if mon.active_workspace.id ~= workspace.id then mon:set_workspace(workspace) end

    -- Если сочетание нажато из игры, фокус остаётся в игре. Если из медиаприложения,
    -- клавиатура переключается вместе с картинкой.
    if previous and (previous.address == spot.address or previous.address == disc.address) then
        hl.dispatch(hl.dsp.focus({ window = target_sel }))
    elseif previous then
        local active = hl.get_active_window()
        if not active or active.address ~= previous.address then
            hl.dispatch(hl.dsp.focus({ window = "address:" .. previous.address }))
        end
    end

    -- В самом конце, чтобы возможный warp при восстановлении фокуса
    -- не вернул курсор обратно на основной монитор. Координаты логические.
    hl.dispatch(hl.dsp.cursor.move({
        x = math.floor(mon.x + width / 2),
        y = math.floor(mon.y + height / 2),
    }))
end, { description = "Spotify <-> Discord на втором мониторе" })
end

-- ----------------------------------------------------------------------------
-- hypr.monitors
-- ----------------------------------------------------------------------------
package.preload["hypr.monitors"] = function(...)
-- See https://wiki.hypr.land/Configuring/Basics/Monitors/
-- List current monitors and supported resolutions with: hyprctl monitors all

local nixos_gdk_scale = 2
local nixos_monitor_scale = 2

hl.env("GDK_SCALE", tostring(nixos_gdk_scale))
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = nixos_monitor_scale })

hl.monitor({
  output = "HDMI-A-3",
  mode = "1920x1080@144",
  position = "0x0",
  scale = 1,
})

hl.monitor({
  output = "HDMI-A-4",
  mode = "1920x1280@60",
  position = "480x1080",
  scale = 2,
})

-- Configure a specific monitor.
-- hl.monitor({ output = "DP-2", mode = "2560x1440@144", position = "0x0", scale = 1 })

-- Portrait/rotated secondary monitor (transform: 1 = 90°, 3 = 270°).
-- hl.monitor({ output = "DP-2", mode = "preferred", position = "auto", scale = 1, transform = 1 })
end

-- ----------------------------------------------------------------------------
-- hypr.no-opacity
-- ----------------------------------------------------------------------------
package.preload["hypr.no-opacity"] = function(...)
-- Без прозрачности: Discord, Spotify, Firefox, AJAZZ, Dota 2, игры Steam и виртуалки.
local opaque = { tag = "-default-opacity", opacity = "1 1" }
local function solid(match)
  local rules = {}
  for k, v in pairs(opaque) do rules[k] = v end
  o.window(match, rules)
end

solid("^([dD]iscord|[vV]esktop|[sS]potify|[fF]irefox)$")
-- Steam: нативные Linux-игры (dota2 и др.) и Proton-игры (steam_app_NNN).
solid("^(dota2|steam_app_.*|gamescope)$")
-- Любое окно, помеченное как игра (content type), — тоже без прозрачности.
solid({ content = "game" })
-- Виртуализация: virt-manager (все его окна, включая консоль ВМ), virt-viewer/remote-viewer,
-- QEMU, Looking Glass, VirtualBox, VMware, GNOME Boxes и Passthru.
solid("^([vV]irt-manager|[vV]irt-viewer|[rR]emote-viewer|.*[qQ]emu.*|[lL]ooking-glass-client|[vV]irtual[bB]ox.*|[vV]mware.*|org\\.gnome\\.Boxes|local\\.passthru\\..*)$")
end

-- ----------------------------------------------------------------------------
-- hypr.spotify-background
-- ----------------------------------------------------------------------------
package.preload["hypr.spotify-background"] = function(...)
-- Плеер работает в фоне (24.11): SUPER+W / SUPER+Q на окне выбранного плеера не закрывают его,
-- а прячут в special:<плеер> — музыка играет, меню Win+B им управляет. Вернуть окно —
-- SUPER+SHIFT+M или SUPER+SHIFT+F. Остальные окна закрываются как обычно.
-- Плеер — файл ~/.config/nixos/media-player: spotify (по умолчанию) или soundcloud.
-- Spotify узнаётся по классу окна, SoundCloud (Chromium --app, app_id chrome-…-Default) —
-- по PID из $XDG_RUNTIME_DIR/soundcloud-app.pid.
-- Если плеер всё же завершился (свой крестик, падение) — служба media-background
-- (home/nextagg.nix) запускает его снова, сразу в special:<плеер>.
local function read_line(path)
  local f = io.open(path, "r")
  if not f then return "" end
  local line = f:read("*l") or ""
  f:close()
  return line
end

local function media_kind()
  local home = os.getenv("HOME") or ""
  local conf = os.getenv("XDG_CONFIG_HOME") or (home .. "/.config")
  local k = read_line(conf .. "/nixos/media-player"):gsub("%s", ""):lower()
  return k == "soundcloud" and "soundcloud" or "spotify"
end

local function soundcloud_pid()
  local run = os.getenv("XDG_RUNTIME_DIR") or ""
  return tonumber((read_line(run .. "/soundcloud-app.pid"):gsub("%s", "")))
end

local function close_or_hide()
  local w = hl.get_active_window()
  local kind = media_kind()
  local mine = false
  if w and kind == "spotify" then
    mine = (w.class or ""):lower() == "spotify"
  elseif w and kind == "soundcloud" then
    local pid = soundcloud_pid()
    mine = pid ~= nil and w.pid == pid
  end
  if mine then
    hl.dispatch(hl.dsp.window.move({ workspace = "special:" .. kind, window = "address:" .. w.address, follow = false }))
  else
    hl.dispatch(hl.dsp.window.close())
  end
end

for _, keys in ipairs({ "SUPER + Q" }) do   -- Win+W убран по просьбе (25.11)
  hl.unbind(keys)
  hl.bind(keys, close_or_hide, { description = "Close window (плеер — в фон)" })
end
end

-- ----------------------------------------------------------------------------
-- hypr.osu-spotify
-- ----------------------------------------------------------------------------
package.preload["hypr.osu-spotify"] = function(...)
-- osu! и Spotify: когда на экране воркспейс с окном osu! — Spotify на паузу,
-- когда уходишь с этого воркспейса (или osu! закрылся) — Spotify снова играет,
-- но только если он играл в момент, когда ты пришёл на воркспейс с osu!.
-- Логику паузы и запоминания делает ~/.local/bin/osu-spotify-pause.

local CMD = os.getenv("HOME") .. "/.local/bin/osu-spotify-pause"

local function is_osu(w)
  local c = (w.class or ""):lower()
  return c:sub(1, 4) == "osu!" -- osu!lazer ("osu!") и osu!stable в wine ("osu!.exe")
end

-- osu! виден: его воркспейс сейчас активный на своём мониторе
local function osu_visible()
  for _, w in ipairs(hl.get_windows()) do
    if is_osu(w) and w.workspace and w.workspace.id then
      local ws = hl.get_workspace(tostring(w.workspace.id))
      local mon = ws and ws.monitor
      local cur = mon and hl.get_active_workspace(mon.name)
      if cur and cur.id == w.workspace.id then return true end
    end
  end
  return false
end

local shown = false

local function update()
  local now = osu_visible()
  if now ~= shown then
    shown = now
    hl.exec_cmd(CMD .. (now and " enter" or " leave"))
  end
end

-- события приходят до того, как состояние окон обновилось; проверяем чуть позже
local function later()
  hl.timer(update, { timeout = 60, type = "oneshot" })
end

hl.on("workspace.active", later)
hl.on("window.open", later)
hl.on("window.destroy", later)
hl.on("window.move_to_workspace", later)
hl.on("config.reloaded", later)
end

-- ----------------------------------------------------------------------------
-- hypr.pin-ghost
-- ----------------------------------------------------------------------------
package.preload["hypr.pin-ghost"] = function(...)
-- SUPER + P: «призрачное» закрепление плавающего окна.
-- Окно закрепляется поверх всех воркспейсов (pin) и становится сквозным:
-- no_focus = клики, наведение и клавиатура проходят в окно под ним.
-- Такое окно нельзя сделать активным, поэтому повторное SUPER + P
-- (из любого окна) открепляет все «призраки».

local TAG = "pin-ghost"

local function has_tag(w)
  for _, t in ipairs(w.tags or {}) do
    if t:gsub("%*$", "") == TAG then return true end
  end
  return false
end

local function notify(text)
  hl.exec_cmd("notify-send -t 2000 -a Hyprland 'Закрепление' '" .. text .. "'")
end

local function ghost(w)
  local sel = "address:" .. w.address
  hl.dispatch(hl.dsp.window.pin({ window = sel }))
  hl.dispatch(hl.dsp.window.alter_zorder({ window = sel, mode = "top" }))
  hl.dispatch(hl.dsp.window.set_prop({ window = sel, prop = "no_focus", value = "1" }))
  hl.dispatch(hl.dsp.window.tag({ window = sel, tag = "+" .. TAG }))
end

local function unghost(w)
  local sel = "address:" .. w.address
  hl.dispatch(hl.dsp.window.set_prop({ window = sel, prop = "no_focus", value = "unset" }))
  hl.dispatch(hl.dsp.window.tag({ window = sel, tag = "-" .. TAG }))
  if w.pinned then hl.dispatch(hl.dsp.window.pin({ window = sel })) end
end

hl.bind("SUPER + P", function()
  -- 1. Есть «призраки» → открепить все
  local n = 0
  for _, w in ipairs(hl.get_windows()) do
    if has_tag(w) then
      unghost(w)
      n = n + 1
    end
  end
  if n > 0 then
    notify("Окно откреплено")
    return
  end

  local active = hl.get_active_window()
  if not active then return end

  -- 2. Активное плавающее окно → закрепить сквозным
  if active.floating and not active.pinned then
    ghost(active)
    notify("Окно закреплено и сквозное. SUPER+P ещё раз — открепить")
  -- 3. Закреплено чем-то другим (например, PiP) → просто открепить
  elseif active.pinned then
    hl.dispatch(hl.dsp.window.pin({ window = "address:" .. active.address }))
  else
    notify("Сначала сделай окно плавающим (SUPER+RETURN)")
  end
end)
end

-- ----------------------------------------------------------------------------
-- hypr.princewm
-- ----------------------------------------------------------------------------
package.preload["hypr.princewm"] = function(...)
-- PrinceWM для Hyprland (порт github.com/Ravestars/PrinceWM): переключатель окон как бесконечный холст.
-- Демон: systemctl --user status princewm. Исходники: ~/Work/princewm-linux.

-- Оверлей сам анимирует открытие/закрытие — фейд слоёв Hyprland ему не нужен.
hl.layer_rule({ match = { namespace = "princewm" }, no_anim = true, animation = "none" })

-- SUPER+TAB раньше занимал плагин оболочки org.lsong.window-switcher (отключён:
-- `nixos plugin enable org.lsong.window-switcher`, чтобы вернуть). ALT+TAB свободен.
local msg = os.getenv("HOME") .. "/.local/bin/princewm-msg"
hl.unbind("SUPER + TAB")
hl.unbind("SUPER + SHIFT + TAB")
o.bind("SUPER + TAB", "PrinceWM: canvas / next window", msg .. " next")
o.bind("SUPER + SHIFT + TAB", "PrinceWM: previous window", msg .. " prev")
end

-- ----------------------------------------------------------------------------
-- hypr.steam-friends
-- ----------------------------------------------------------------------------
package.preload["hypr.steam-friends"] = function(...)
-- Steam при каждом запуске сам открывает «Список друзей» (настройкой не отключается).
-- Закрываем это окно, только если процесс Steam (steamwebhelper) запущен меньше 45 с назад:
-- открытый вручную позже список друзей не трогаем.
local TITLES = { ["Список друзей"] = true, ["Friends List"] = true }
local MAX_AGE = 45

local function read(path)
  local f = io.open(path, "r")
  if not f then return nil end
  local s = f:read("*a")
  f:close()
  return s
end

-- Возраст процесса в секундах: starttime (поле 22 /proc/pid/stat, в тиках по 1/100 с) против uptime.
local function process_age(pid)
  local stat, uptime = read("/proc/" .. pid .. "/stat"), read("/proc/uptime")
  if not stat or not uptime then return nil end
  local fields = {}
  for v in stat:match("%) (.*)"):gmatch("%S+") do fields[#fields + 1] = v end
  local start = tonumber(fields[20]) -- после «pid (comm)» поле 22 становится 20-м
  return start and (tonumber(uptime:match("^%S+")) - start / 100)
end

local function maybe_close(w)
  if not w or w.class ~= "steam" or not TITLES[w.title] then return end
  local age = process_age(w.pid)
  if age and age < MAX_AGE then
    hl.dispatch(hl.dsp.window.close({ window = "address:" .. w.address }))
  end
end

hl.on("window.open", maybe_close)
hl.on("window.title", maybe_close)
end

-- ----------------------------------------------------------------------------
-- hypr.vlnblox
-- ----------------------------------------------------------------------------
package.preload["hypr.vlnblox"] = function(...)
-- Создано лаунчером vlnblox. Удаляется из лаунчера: Главная → Шейдеры → «Меню в игре по Home».
-- Home в окне Roblox (Sober) открывает и закрывает меню шейдеров, в остальных окнах — обычная клавиша Home.

local function vlnblox_is_game(w)
  return w and (w.class == "org.vinegarhq.Sober" or w.title == "vlnblox-overlay")
end

local function vlnblox_home()
  if vlnblox_is_game(hl.get_active_window()) then
    hl.exec_cmd("/opt/vlnblox/vlnblox --overlay")
    return
  end
  -- Не игра: отдаём Home активному окну, как будто бинда нет.
  hl.dispatch(hl.dsp.send_key_state({ mods = "", key = "Home", state = "down" }))
  hl.timer(function()
    hl.dispatch(hl.dsp.send_key_state({ mods = "", key = "Home", state = "up" }))
  end, { timeout = 50, type = "oneshot" })
end

o.bind("Home", "vlnblox: меню шейдеров в Roblox", vlnblox_home)

-- Меню поверх игры: плавающее и закреплённое. Пока открыто, держит фокус — Roblox отпускает курсор
-- и по кнопкам меню можно кликать. Полноэкранную игру это не сворачивает: правило
-- misc.on_focus_under_fullscreen касается только тайловых окон.
o.window({ class = "vlnblox", title = "^vlnblox-overlay$" }, { float = true, pin = true, center = true, stay_focused = true })
end

-- ----------------------------------------------------------------------------
-- hypr.workspace-switch
-- ----------------------------------------------------------------------------
package.preload["hypr.workspace-switch"] = function(...)
-- Плавное переключение воркспейсов 1–4 (скольжение по горизонтали).
-- Воркспейс 5 один на HDMI-A-4, там смены воркспейса не бывает — анимация его не касается.
-- easeInOutCubic: мягкий разгон и торможение — без рывка в первом кадре.
hl.curve("wsSmooth", { type = "bezier", points = { { 0.65, 0 }, { 0.35, 1 } } })

local WS_ANIM = { leaf = "workspaces", enabled = true, speed = 5, bezier = "wsSmooth", style = "slide" }
hl.animation(WS_ANIM)

-- Если на мониторе, куда переключаемся, сейчас окно во весь экран — переключаемся мгновенно.
local function go(ws)
  local target = hl.get_workspace(ws)
  local mon = target and target.monitor
  local cur = mon and hl.get_active_workspace(mon.name)
  if cur and cur.has_fullscreen and tostring(cur.id) ~= ws then
    hl.animation({ leaf = "workspaces", enabled = false })
    hl.dispatch(hl.dsp.focus({ workspace = ws }))
    -- вернуть анимацию сразу нельзя — переключение её подхватит; ждём, пока оно применится
    hl.timer(function() hl.animation(WS_ANIM) end, { timeout = 100, type = "oneshot" })
  else
    hl.dispatch(hl.dsp.focus({ workspace = ws }))
  end
end

for n = 1, 4 do   -- Win+5 — свой бинд в hypr.bindings (воркспейс 5 на втором мониторе, без анимации)
  hl.bind("SUPER + " .. n, function() go(tostring(n)) end)
end
end

-- ============================================================================
-- 4. Main
-- ============================================================================
-- Learn how to configure Hyprland: https://wiki.hypr.land/Configuring/Start/

-- NixOS's bootstrap keeps path setup out of this user config.

-- Disable all NixOS default bindings. Add your own in hypr/bindings.lua.
-- nixos_default_bindings = false
--
-- Or disable only bindings for NixOS's preinstalled apps/web apps while
-- keeping core window-manager bindings:
-- nixos_preinstalled_bindings = false

-- Load NixOS defaults.
nixos_default_bindings = false
-- NixOS 4.5 gives each monitor its own workspace block (HDMI-A-4 would get 11-20),
-- which renumbers ws 5 and hides Spotify/Discord. Keep the workspace rules from bindings.lua.
package.preload["default.hypr.monitor-workspaces"] = function() return {} end
require("default.hypr.nixos")

-- Put your personal overrides in these files. They're loaded after NixOS's
-- defaults so package updates can improve the defaults without rewriting your
-- ~/.config/hypr files.
-- share: require("hypr.monitors")
require("hypr.input")
require("hypr.bindings")
require("hypr.pin-ghost") -- SUPER+P: сквозное закрепление плавающих окон
require("hypr.looknfeel")
require("hypr.workspace-switch")
require("hypr.appearance")
-- share: require("hypr.autostart")
-- share: require("hypr.princewm") -- PrinceWM: Alt+Tab canvas
-- share: require("media-toggle")

pcall(require, "hypr.gui-settings") -- Hypr Settings: настройки из GUI (загружается последним)

-- Toggle config flags dynamically.
require("default.hypr.toggles")

-- Add any other personal Hyprland configuration below.
-- o.window("qemu", { workspace = "5" })
o.window({ class = "steam", title = "Steam" }, { float = false })
-- About (fastfetch с широким логотипом NixOS): свой конфиг fastfetch отключает автоподгонку окна
o.window("org.nixos.about", { size = { 840, 520 } })

require("hypr.no-opacity")
-- share: require("hypr.steam-friends") -- закрывать «Список друзей», который Steam открывает при запуске
-- share: require("hypr.osu-spotify") -- osu! на экране: Spotify на паузу, ушёл — играет снова (если играл)
require("hypr.spotify-background") -- SUPER+W/Q на окне выбранного плеера прячут его в фон, а не закрывают
-- share: require("hypr.deadlock") -- Deadlock: полный экран, tearing, монитор 144 Гц

pcall(require, "hypr.vlnblox") -- vlnblox: меню шейдеров Home
