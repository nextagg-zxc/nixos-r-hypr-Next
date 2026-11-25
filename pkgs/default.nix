{ pkgs, inputs, self }:
# Самоссылки — через own (этот же набор), а не self.packages: тогда набор можно собрать и на
# другом nixpkgs (передать свой pkgs), не смешивая ветки.
let
  own = import ./default.nix { inherit pkgs inputs self; };
  nixos-desktop = pkgs.callPackage ./nixos-desktop.nix { src = inputs.desktop-src; };
  owe = pkgs.callPackage ./owe.nix { src = inputs.owe; };
in
{
  inherit nixos-desktop owe;

  # Quickshell как в upstream 4.5: ревизия 2b4501a + патч загрузки плагинов (прагма NixOSLoadPatch,
  # переименована вместе со всем рабочим столом).
  quickshell = pkgs.quickshell.overrideAttrs (old: {
    version = "0.3.2-unstable-nixos";
    src = inputs.quickshell-src;
    patches = (old.patches or [ ]) ++ [ ../patches/quickshell-nixos-load.patch ];
  });

  # Mesa из main (nextagg.mesa.source = "git" на хосте).
  mesa-git = pkgs.callPackage ./mesa-git.nix {
    src = inputs.mesa-git;
    rev = builtins.substring 0 8 (inputs.mesa-git.rev or "git");
  };

  millennium = pkgs.callPackage ./millennium { };
  omacalc = pkgs.callPackage ./omacalc.nix { };
  nixos-desktop-fonts = pkgs.callPackage ./desktop-fonts { };
  extra-icons = pkgs.callPackage ./extra-icons { };
  mise-bin = pkgs.callPackage ./mise-bin { };
  wallpapers = pkgs.callPackage ./wallpapers.nix { };
  # SoundCloud окном Chromium (MPRIS для меню Win+B), см. PlayerPick.js в плагине меню.
  soundcloud-app = pkgs.callPackage ./soundcloud-app.nix { };
  # «Автозапуск»: записи XDG autostart, задержка и скрытый запуск (autostart-run).
  autostart = pkgs.callPackage ./autostart { };
  # KDE «как Windows 11/10» для раздаваемой системы (темы, оформление, nixos-kde-look).
  kde-windows = pkgs.callPackage ./kde-windows { };
  # «Настройка системы» раздаваемой системы (окно + root-помощник nixos-share-apply).
  system-settings = pkgs.callPackage ./system-settings { };
  # «Магазин» раздаваемой системы (nixpkgs + Flathub).
  store = pkgs.callPackage ./store { system-settings = own.system-settings; };
  # Малые программы друзей: .exe/AppImage, шпаргалка, отчёт о проблеме, удалённая помощь.
  newbie-tools = pkgs.callPackage ./newbie-tools { };
  # Установщик ISO для друзей: Calamares со страницами выбора + шаг установки (nixos-share-install).
  share-installer = pkgs.callPackage ./share-installer { };

  # Сторонние плагины и темы одной папкой: share/desktop-extras/{plugins,themes}/<id>.
  desktop-extras = pkgs.callPackage ./extras.nix { inherit inputs; };

  # Весь твой вид (dotfiles + плагины + темы + меню для NixOS) одной папкой.
  # Его раскладывает home-manager (modules/home/look.nix).
  desktop-look = pkgs.callPackage ./look.nix {
    wallpapers = own.wallpapers;
    inherit self nixos-desktop;
    extras = own.desktop-extras;
  };

  # Тот же вид для друзей — без личного (scripts/share-profile.py).
  desktop-look-share = own.desktop-look.override { profile = "share"; };

  default = nixos-desktop;
}
