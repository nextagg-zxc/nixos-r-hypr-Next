{ inputs, self }:
{ config, lib, pkgs, osConfig ? { }, ... }:

# Твой вид рабочего стола в домашней папке: бар, меню, плагины, темы, hypr, терминалы.
#
# Файлы КОПИРУЮТСЯ, а не ссылаются в /nix/store: рабочий стол сам пишет в
# shell.json (перетаскивание виджетов), hypr/gui-settings.lua (Hypr Settings),
# ~/.local/state/nixos (смена темы). Источник правды — dotfiles/ в репозитории:
#   правки через GUI → меню Packages → «Сохранить вид в конфиг» → git commit.
let
  cfg = config.nextagg.look;
  ownPkgs = osConfig.nextagg.ownPackages or self.packages.${pkgs.stdenv.hostPlatform.system};
  # share — вид для друзей без личного (scripts/share-profile.py)
  look = if cfg.profile == "share" then ownPkgs.desktop-look-share else ownPkgs.desktop-look;
  desktopPkg = ownPkgs.nixos-desktop;
  rsync = "${pkgs.rsync}/bin/rsync";
in
{
  options.nextagg.look = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Разложить вид рабочего стола в ~/.config.";
    };
    profile = lib.mkOption {
      type = lib.types.enum [ "personal" "share" ];
      default = "personal";
      description = "share — вид для друзей: без личных плагинов, пунктов меню и модулей Hyprland.";
    };
    overwrite = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        При каждом применении конфига перезаписывать ~/.config/nixos, ~/.config/hypr
        и остальное версией из репозитория. false — только докладывать недостающее.
      '';
    };
    theme = lib.mkOption {
      type = lib.types.str;
      default =
        let f = "${../../dotfiles}/nixos/theme.name";
        in if builtins.pathExists f then lib.removeSuffix "\n" (builtins.readFile f) else "neovoid";
      description = "Тема при первом входе (папка в ~/.config/nixos/themes или встроенная).";
    };
  };

  config = lib.mkIf cfg.enable {
    home.activation.desktopLook = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      src=${look}/share/nixos-look

      # 0б. Стартовая настройка (nixos-provision-first-run) рассчитана на
      #    другой дистрибутив: на NixOS два её шага падают, и она на каждом входе заново шлёт
      #    «Update System / Setup Git / Learn Keybindings». Всё это уже сделано
      #    этим модулем — помечаем её выполненной.
      mkdir -p "$HOME/.local/state/nixos/done"
      touch "$HOME/.local/state/nixos/done/first-run-user"

      # 1. Стандартные конфиги рабочего стола (как делает установщик) — только недостающие.
      #    Кроме hypr: весь конфиг Hyprland — один hyprland.lua из вида (шаг 2).
      run ${rsync} -a --ignore-existing --chmod=u+w --exclude=/hypr/ ${desktopPkg}/share/nixos/config/ "$HOME/.config/"

      # 2. Твой вид поверх.
      if ${lib.boolToString cfg.overwrite}; then
        run ${rsync} -a --chmod=u+w "$src/home/" "$HOME/"
      else
        run ${rsync} -a --ignore-existing --chmod=u+w "$src/home/" "$HOME/"
      fi

      # 3. Тема и обои — только если ещё не выбраны (дальше меняешь через меню Appearance).
      state="$HOME/.local/state/nixos/current"
      if [ ! -s "$state/theme.name" ]; then
        run mkdir -p "$state"
        run env NIXOS_PATH=/usr/share/nixos NIXOS_THEME_HEADLESS=1 \
          PATH="${desktopPkg}/bin:/run/current-system/sw/bin:$PATH" \
          nixos-theme-set ${lib.escapeShellArg cfg.theme} || echo "nixos-theme-set: тема применится при входе"
        if [ -s "$src/background" ]; then
          bg=$(sed "s|^~/|$HOME/|" "$src/background")
          [ -e "$bg" ] && run ln -snf "$bg" "$state/background"
        fi
      fi
    '';

    # Курсоры Material Design (из dotfiles/icons), как в looknfeel.lua.
    home.pointerCursor = lib.mkDefault {
      enable = true;
      name = "material-design-dark";
      package = look; # share/icons/material-design-dark
      size = 26;
      gtk.enable = true;
    };

    gtk = {
      enable = true;
      theme = {
        name = "Adwaita-dark";
        package = pkgs.gnome-themes-extra;
      };
    };
    dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-dark";
  };
}
