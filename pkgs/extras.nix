{ lib, runCommand, applyPatches, inputs }:

# Сторонние плагины бара и темы рабочего стола из входов flake (зафиксированы по коммитам).
# Твои локальные правки лежат в patches/ и накладываются здесь.
let
  plugins = {
    "0xfanko.advanced-clipboard" = inputs.plugin-advanced-clipboard;
    "custom.rounded-corner-blur" = inputs.plugin-rounded-corner-blur;
    "io.github.aaronshahriari.omatube" = inputs.plugin-tube;
    "io.github.iampoul.hackernews" = inputs.plugin-hackernews;
    "io.github.jburchel.jarvis" = inputs.plugin-jarvis;
    "jmthomas00.vantage" = inputs.plugin-vantage;
    "ngnk.glass-weather" = inputs.plugin-glass-weather;
    "nixos-resizeable.resizeable" = inputs.plugin-resizeable;
    "org.lsong.window-switcher" = inputs.plugin-window-switcher;
    "sky.lofi" = inputs.plugin-lofi;
    "sys-monitor" = applyPatches {
      name = "sys-monitor-patched";
      src = inputs.plugin-sys-monitor;
      patches = [ ../patches/sys-monitor-bar.patch ];
    };
    "whimsy" = inputs.plugin-whimsy;
  };

  themes = {
    drac = inputs.theme-drac;
    neovoid = applyPatches {
      name = "neovoid-patched";
      src = inputs.theme-neovoid;
      patches = [ ../patches/neovoid-alacritty.patch ];
      # Всё в одном стиле с баром (24.11): палитра Catppuccin Mocha + лавандовый акцент.
      # Статичные файлы темы (голубые) убраны — генератор тем делает их из colors.toml.
      postPatch = ''
        cp ${../overrides/neovoid-colors.toml} colors.toml
        rm -f alacritty.toml btop.theme chromium.theme hyprland.conf hyprlock.conf \
          mako.ini neovim.lua swayosd.css walker.css waybar.css
      '';
    };
    omacarchy = inputs.theme-carchy;
    purple-moon = inputs.theme-purple-moon;
    rainynight = inputs.theme-rainynight;
    void = inputs.theme-void;
  };

  copyAll = dir: set: lib.concatStringsSep "\n" (lib.mapAttrsToList (name: src: ''
    cp -r --no-preserve=mode ${src} "$out/share/desktop-extras/${dir}/${name}"
  '') set);
in
runCommand "desktop-extras" { } ''
  mkdir -p $out/share/desktop-extras/plugins $out/share/desktop-extras/themes
  ${copyAll "plugins" plugins}
  ${copyAll "themes" themes}
  # Исполняемые скрипты плагинов (drives.sh и т.п.) после --no-preserve=mode.
  find $out/share/desktop-extras -name '*.sh' -exec chmod +x {} +
''
