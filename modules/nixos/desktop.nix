{ inputs, self }:
{ config, lib, pkgs, ... }:

# Общий рабочий стол: Hyprland + шелл на Quickshell (upstream 4.5, переименован в nixos-*).
# Это подключают и друзья на NixOS:
#   imports = [ nextagg.nixosModules.desktop ];
#   nextagg.desktop.user = "имя";
let
  cfg = config.nextagg.desktop;
  # свои пакеты флейка (опция — чтобы хост мог подставить набор, собранный на другом nixpkgs)
  ownPkgs = config.nextagg.ownPackages;
  desktopPkg = ownPkgs.nixos-desktop;
  owe = ownPkgs.owe;
  flake = cfg.flakePath;

  # Python для GTK4-программ (/usr/bin/python3 и python3 в PATH). Из меню они
  # запускаются через systemd (uwsm), а там нет GI_TYPELIB_PATH — его даёт только
  # обёртка Ghostty, поэтому из терминала всё работало, а из меню было
  # «Namespace Gtk not available». Схемы GTK4 — для диалогов выбора файлов.
  giLibs = with pkgs; [
    glib gobject-introspection gtk4 libadwaita vte-gtk4 pango gdk-pixbuf graphene harfbuzz librsvg
  ];
  guiPython = pkgs.symlinkJoin {
    name = "python3-gui";
    paths = [ (pkgs.python3.withPackages (ps: [ ps.pygobject3 ])) ];
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      py=$out/bin/python${pkgs.python3.pythonVersion}
      wrapProgram $py \
        --prefix GI_TYPELIB_PATH : ${lib.makeSearchPathOutput "out" "lib/girepository-1.0" giLibs} \
        --prefix XDG_DATA_DIRS : ${pkgs.gtk4}/share/gsettings-schemas/${pkgs.gtk4.name}
      ln -sf $(basename $py) $out/bin/python3
      ln -sf $(basename $py) $out/bin/python
    '';
  };

  # Тема экрана входа SDDM (default/sddm/nixos) в том месте, где её ищет NixOS.
  sddmTheme = pkgs.runCommand "sddm-theme-nixos" { } ''
    mkdir -p $out/share/sddm/themes
    cp -r ${desktopPkg}/share/nixos/default/sddm/nixos $out/share/sddm/themes/nixos
  '';

  # Команды для пунктов меню Packages/Update (overrides/menu-nixos.jsonc).
  helpers = [
    (pkgs.writeShellScriptBin "nextagg-rebuild" ''
      set -e
      cd ${lib.escapeShellArg flake}
      git add -A >/dev/null 2>&1 || true
      sudo nixos-rebuild switch --flake ".#$(hostname)" "$@"
      nixos-restart-shell >/dev/null 2>&1 || true
      echo; echo "Готово. Если что-то сломалось — меню Update → Откатить систему."
    '')
    (pkgs.writeShellScriptBin "nextagg-update" ''
      set -e
      cd ${lib.escapeShellArg flake}
      nix flake update nixpkgs home-manager
      # своё, что обновляется не через flake (например, Millennium из релизов GitHub)
      for hook in scripts/update.d/*; do
        [ -x "$hook" ] && "$hook" || true
      done
      nextagg-rebuild "$@"
    '')
    (pkgs.writeShellScriptBin "nextagg-rollback" ''
      set -e
      sudo nixos-rebuild switch --rollback
      echo "Откатился на предыдущую сборку."
    '')
    (pkgs.writeShellScriptBin "nextagg-gc" ''
      set -e
      sudo nix-collect-garbage --delete-older-than 7d
      nix-collect-garbage --delete-older-than 7d
    '')
    # cfg [запрос] — список файлов flake (fzf с превью), Enter — правка в nano, Esc — выход.
    (pkgs.writeShellScriptBin "nextagg-config" ''
      set -eo pipefail
      cd ${lib.escapeShellArg flake}
      export PATH=${lib.makeBinPath [ pkgs.fzf pkgs.nano pkgs.bat pkgs.git pkgs.gnugrep pkgs.gawk pkgs.coreutils ]}:$PATH
      {
        printf '%s\n' flake.nix hosts/nextagg/default.nix
        git ls-files --cached --others --exclude-standard 2>/dev/null || find . -type f -not -path './.git/*' -printf '%P\n'
      } | grep -vE '\.(png|jpe?g|gif|webp|ico|svg|gz|xz|zst|tar|foz|bin)$' | awk '!seen[$0]++' |
        fzf --prompt='конфиг> ' --query="''${1:-}" \
          --header='Enter — открыть в nano · Esc — выход · применить: rebuild' \
          --preview='bat --color=always --style=numbers {}' --preview-window=right,60% \
          --bind='enter:execute(nano {})' >/dev/null || true
    '')
    # Быстрые строки fastfetch (24.11): подсчёт пакетов nix ~120 мс → кэш до следующей сборки
    # или изменения flatpak; версия терминала из TERM_PROGRAM_VERSION вместо `ghostty --version`.
    (pkgs.writeShellScriptBin "nextagg-ff" ''
      ff=${pkgs.fastfetch}/bin/fastfetch
      case "''${1:-}" in
        terminal)
          if [ -n "''${TERM_PROGRAM:-}" ]; then
            echo "$TERM_PROGRAM ''${TERM_PROGRAM_VERSION:-}"
          else
            $ff -c ${pkgs.writeText "ff-terminal.jsonc" ''
              { "logo": { "type": "none" }, "display": { "pipe": true, "separator": "" },
                "modules": [ { "type": "terminal", "key": " ", "keyWidth": 0, "format": "{pretty-name} {version}" } ] }
            ''}
          fi ;;
        packages)
          cache=''${XDG_CACHE_HOME:-$HOME/.cache}/nextagg-ff-packages
          key="$(readlink /run/current-system "/etc/profiles/per-user/$USER" "$HOME/.nix-profile" 2>/dev/null
                 stat -c %Y "$HOME/.local/share/flatpak/app" /var/lib/flatpak/app 2>/dev/null)"
          if [ -f "$cache" ] && [ "$(head -n -1 "$cache")" = "$key" ]; then
            tail -n 1 "$cache"
            exit 0
          fi
          value=$($ff -c ${pkgs.writeText "ff-packages.jsonc" ''
            { "logo": { "type": "none" }, "display": { "pipe": true, "separator": "" },
              "modules": [ { "type": "packages", "key": " ", "keyWidth": 0,
                "format": "{nix-system} nix · {nix-user} user · {flatpak-user} flatpak" } ] }
          ''})
          mkdir -p "''${cache%/*}"
          printf '%s\n%s\n' "$key" "$value" > "$cache.$$" && mv -f "$cache.$$" "$cache"
          echo "$value" ;;
        *) echo "usage: nextagg-ff terminal|packages" >&2; exit 1 ;;
      esac
    '')
    (pkgs.writeShellScriptBin "nextagg-save-look" ''
      set -e
      ${lib.escapeShellArg flake}/scripts/collect-dotfiles.sh
      cd ${lib.escapeShellArg flake} && git status --short dotfiles | head -40
    '')
  ];
in
{
  # Zapret Hub — всегда (дизайн раздаваемой системы): программа, служба nfqws, права pkexec.
  imports = [ "${inputs.zapret-hub}/packaging/nixos/module.nix" ./gamemode.nix ];

  options.nextagg.ownPackages = lib.mkOption {
    type = lib.types.attrsOf lib.types.package;
    default = self.packages.${pkgs.stdenv.hostPlatform.system};
    defaultText = lib.literalExpression "self.packages.\${system}";
    description = "Набор своих пакетов флейка (должен быть собран на той же ветке nixpkgs, что система).";
  };

  # распознавание текста на скриншотах; раздаваемая система берёт меньше языков (весь набор — 1 ГиБ)
  options.nextagg.tesseract = lib.mkOption {
    type = lib.types.package;
    default = pkgs.tesseract;
    description = "tesseract для OCR рабочего стола";
  };

  options.nextagg.desktop = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Рабочий стол (Hyprland + бар + меню).";
    };
    user = lib.mkOption {
      type = lib.types.str;
      description = "Пользователь, для которого включается автологин и вид.";
    };
    autoLogin = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Входить без пароля (диск и так зашифрован LUKS).";
    };
    flakePath = lib.mkOption {
      type = lib.types.str;
      default = "/home/${cfg.user}/nixos-config";
      description = "Где лежит этот репозиторий (для пунктов меню и nextagg-rebuild).";
    };
  };

  config = lib.mkIf cfg.enable {
    services.zapret-hub.enable = lib.mkDefault true;

    nix.settings = {
      experimental-features = [ "nix-command" "flakes" ];
      auto-optimise-store = true;
    };

    # ── Hyprland через uwsm (uwsm-app в меню и биндах) ──
    programs.hyprland = {
      enable = true;
      withUWSM = true;
      xwayland.enable = true;
    };
    xdg.portal.extraPortals = [ pkgs.xdg-desktop-portal-gtk ];

    services.displayManager = {
      defaultSession = "hyprland-uwsm";
      autoLogin = lib.mkIf cfg.autoLogin {
        enable = true;
        user = cfg.user;
      };
      sddm = {
        enable = true;
        wayland.enable = true;
        package = lib.mkDefault pkgs.kdePackages.sddm;
        theme = "nixos";
        extraPackages = [ pkgs.kdePackages.qtsvg pkgs.kdePackages.qtdeclarative ];
      };
    };

    # ── Рабочий стол в /usr/share/nixos ──
    # Все скрипты и QML ищут его по NIXOS_PATH или по этому пути.
    systemd.tmpfiles.rules = [
      "d /usr/share 0755 root root -"
      "L+ /usr/share/nixos - - - - ${desktopPkg}/share/nixos"
      # Смена темы перекрашивает акцент Chromium через sudo по этому пути.
      "L+ /usr/bin/nixos-theme-set-browser-policy - - - - ${desktopPkg}/share/nixos/bin/nixos-theme-set-browser-policy"
      # Плагины в dotfiles вызывают /usr/bin/python3 напрямую.
      "L+ /usr/bin/python3 - - - - ${guiPython}/bin/python3"
      # Многие скрипты начинаются с #!/bin/bash, а в NixOS в /bin есть только sh.
      "L+ /bin/bash - - - - ${pkgs.bashInteractive}/bin/bash"
      "L+ /usr/bin/bash - - - - ${pkgs.bashInteractive}/bin/bash"
      "L+ /usr/bin/xdg-open - - - - ${pkgs.xdg-utils}/bin/xdg-open"
      # плагины бара (advanced-clipboard, omatube) зовут их по полным путям /usr/bin
      "L+ /usr/bin/kill - - - - ${pkgs.util-linux}/bin/kill"
      "L+ /usr/bin/setpriv - - - - ${pkgs.util-linux}/bin/setpriv"
      "L+ /usr/bin/setsid - - - - ${pkgs.util-linux}/bin/setsid"
      # ярлыки системных программ там, где их ищут скрипты (/usr/share/applications)
      "L+ /usr/share/applications - - - - /run/current-system/sw/share/applications"
    ];
    # Окружение сессии (/etc/xdg/uwsm/env.d):
    # ~/.local/bin в PATH, TERMINAL=xdg-terminal-exec, EDITOR. uwsm из nixpkgs
    # ищет env.d в XDG-каталогах настроек, поэтому кладём в /etc/xdg.
    environment.etc."xdg/uwsm/env.d/10-nixos".source = "${desktopPkg}/share/nixos/default/uwsm/env.d/10-nixos";

    environment.sessionVariables = {
      # Схемы GSettings для nixos-theme-set-gnome (тёмная тема GTK, акцент).
      XDG_DATA_DIRS = [
        "${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}"
        "${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}"
      ];
      NIXOS_PATH = "/usr/share/nixos";
      NEXTAGG_FLAKE = flake;
    };

    # Экран блокировки шелла проверяет пароль через PAM-сервис nixos-lock-password.
    security.pam.services.nixos-lock-password = { };
    security.pam.services.nixos-lock-fingerprint = { };
    security.polkit.enable = true;
    # То же правило, что etc/sudoers.d/nixos-theme-browser: без пароля и
    # только с аргументом из шести hex-цифр (цвет акцента).
    security.sudo.extraConfig = ''
      %wheel ALL=(root) NOPASSWD: /usr/bin/nixos-theme-set-browser-policy [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]
    '';
    services.gnome.gnome-keyring.enable = true;
    security.pam.services.sddm.enableGnomeKeyring = true;

    # ── Звук, сеть, bluetooth, питание, флешки ──
    services.pipewire = {
      enable = true;
      alsa.enable = true;
      pulse.enable = true;
      wireplumber.enable = true;
    };
    security.rtkit.enable = true;
    networking.networkmanager.enable = true;
    hardware.bluetooth.enable = true;
    services.power-profiles-daemon.enable = true;
    services.upower.enable = true;
    services.udisks2.enable = true;
    services.gvfs.enable = true;
    services.avahi = {
      enable = true;
      nssmdns4 = true;
    };
    programs.dconf.enable = true;

    # Движок обоев (owe): owed стартует с графической сессией.
    systemd.user.services.owed = {
      description = "owe wallpaper engine daemon";
      partOf = [ "graphical-session.target" ];
      after = [ "graphical-session.target" ];
      wantedBy = [ "graphical-session.target" ];
      environment.NIXOS_PATH = "/usr/share/nixos";
      path = with pkgs; [ bash coreutils findutils gnugrep gnused gawk socat jq ];
      serviceConfig = {
        ExecStart = "${pkgs.bash}/bin/bash -c 'exec ${owe}/bin/owed --prepare-intro \"$(/usr/share/nixos/bin/nixos-theme-bg-boot-intro --resolve-startup 2>/dev/null)\"'";
        Restart = "on-failure";
        RestartSec = 2;
      };
    };

    # ── Шрифты (бар и терминал — FiraCode Nerd Font, как сейчас) ──
    fonts = {
      packages = with pkgs; [
        nerd-fonts.fira-code
        nerd-fonts.jetbrains-mono
        noto-fonts
        noto-fonts-cjk-sans
        noto-fonts-color-emoji
        font-awesome
        liberation_ttf
        ia-writer-mono ia-writer-duospace ia-writer-quattro
        ownPkgs.nixos-desktop-fonts # шрифт значков рабочего стола (nixos.ttf)
      ];
      fontconfig.defaultFonts = {
        monospace = [ "FiraCode Nerd Font" "JetBrainsMono Nerd Font" ];
        sansSerif = [ "Noto Sans" ];
        serif = [ "Noto Serif" ];
        emoji = [ "Noto Color Emoji" ];
      };
    };

    # ── Программы, которые вызывают скрипты и плагины рабочего стола ──
    environment.systemPackages = (with pkgs; [
      desktopPkg owe sddmTheme
      ownPkgs.quickshell uwsm xdg-terminal-exec xdg-utils
      # то, что рабочий стол запускает сам: калькулятор (Super+Shift+Q), сервер агентов
      # при старте, курсор при старте сессии
      ownPkgs.omacalc xsetroot
      # herdr (сервер агентов) есть только в unstable; на stable (хост share) его нет и он не нужен
      (if pkgs ? herdr then pkgs.herdr else xsetroot)
      # ttfx — эффекты скринсейвера (nixos-screensaver). В nixpkgs его нет, есть тот же по ключам
      # TerminalTextEffects (tte). Скрипт ищет процесс по имени ttfx (pgrep -x), поэтому это сам
      # Python-скрипт с именем ttfx, а не обёртка: иначе имя процесса другое и скринсейвер
      # запускал бы ttfx без конца.
      (writeTextFile {
        name = "ttfx";
        destination = "/bin/ttfx";
        executable = true;
        text = ''
          #!${python3}/bin/python3
          import sys
          sys.path.insert(0, "${python3Packages.terminaltexteffects}/${python3.sitePackages}")
          from terminaltexteffects.__main__ import main
          sys.exit(main())
        '';
      })
      gtk3 # gtk-launch: так меню и лаунчер запускают приложения
      vips # vipsthumbnail: миниатюры в выборе обоев (двойной клик по рабочему столу)
      # оболочка скриптов
      bash gum jq git perl libxkbcommon glib curl wget socat inotify-tools libnotify procps psmisc
      util-linux findutils gnused gawk coreutils file unzip lsof pciutils usbutils
      guiPython
      # Wayland-утилиты
      wl-clipboard cliphist grim slurp satty hyprpicker hyprsunset
      brightnessctl ddcutil playerctl pamixer pavucontrol wireplumber
      networkmanagerapplet bluez bluez-tools udiskie
      wf-recorder gpu-screen-recorder
      # терминалы и TUI из меню
      ghostty alacritty foot kitty btop fastfetch starship eza bat fzf ripgrep fd
      lazygit neovim tmux tldr man-pages
      # файлы, картинки, видео
      nautilus sushi imv mpv ffmpeg ffmpegthumbnailer imagemagick evince
      gnome-disk-utility localsend
      # ввод (fcitx5 есть в твоём конфиге)
      kdePackages.qtwayland kdePackages.qtsvg kdePackages.qtimageformats kdePackages.qtmultimedia
      # курсоры и иконки по умолчанию
      # Yaru-* — тема иконок (nixos-theme-set-gnome ставит Yaru-<цвет>);
      # без неё бар, трей и уведомления рисуют вместо иконок фиолетово-чёрный квадрат.
      yaru-theme adwaita-icon-theme hicolor-icon-theme gnome-themes-extra
      config.nextagg.tesseract
    ]) ++ helpers;

    i18n.inputMethod = {
      enable = true;
      type = "fcitx5";
      fcitx5.waylandFrontend = true;
    };

    environment.pathsToLink = [ "/share/nixos" "/share/sddm" ];
  };
}
