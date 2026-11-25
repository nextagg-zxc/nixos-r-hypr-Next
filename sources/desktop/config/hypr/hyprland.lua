-- Learn how to configure Hyprland: https://wiki.hypr.land/Configuring/Start/

-- NixOS's bootstrap keeps path setup out of this user config.
dofile((os.getenv("NIXOS_PATH") or "/usr/share/nixos") .. "/default/hypr/bootstrap.lua")

-- Disable all NixOS default bindings. Add your own in hypr/bindings.lua.
-- nixos_default_bindings = false
--
-- Or disable only bindings for NixOS's preinstalled apps/web apps while
-- keeping core window-manager bindings:
-- nixos_preinstalled_bindings = false

-- Load NixOS defaults.
require("default.hypr.nixos")

-- Put your personal overrides in these files. They're loaded after NixOS's
-- defaults so package updates can improve the defaults without rewriting your
-- ~/.config/hypr files.
require("hypr.monitors")
require("hypr.input")
require("hypr.bindings")
require("hypr.looknfeel")
require("hypr.autostart")

-- Toggle config flags dynamically.
require("default.hypr.toggles")

-- Add any other personal Hyprland configuration below.
-- o.window("qemu", { workspace = "5" })
