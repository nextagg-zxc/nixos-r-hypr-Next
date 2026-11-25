{
  description = "nextagg: NixOS с рабочим столом Hyprland + Quickshell (бар mechabar, меню, темы) одним конфигом";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Secure Boot твоими ключами sbctl (только для основного ПК).
    # Ядро CachyOS (патчи + настройки CachyOS) в виде пакетов Nix.
    nix-cachyos-kernel = {
      url = "github:xddxdd/nix-cachyos-kernel";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Mesa из ветки main — nextagg.mesa.source = "git" (по умолчанию "stable").
    # Mesa 26.2.5: на 26.3.0 Cyberpunk ловил GPU hang (регрессия ANV,
    # не найдена), а в main для Xe2 по умолчанию компилятор Jay (артефакты в Cyberpunk).
    mesa-stable = {
      url = "gitlab:mesa/mesa/mesa-26.2.5?host=gitlab.freedesktop.org";
      flake = false;
    };
    mesa-git = {
      url = "gitlab:mesa/mesa/main?host=gitlab.freedesktop.org";
      flake = false;
    };

    # Spotify с темой Spicetify (StarryNight Lite).
    spicetify-nix = {
      url = "github:Gerg-L/spicetify-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    lanzaboote = {
      url = "github:nix-community/lanzaboote";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Исходники рабочего стола (upstream 4.5.0, уже переименованные копии в ~/Work/nixos-sources);
    # при сборке переименовываются в nixos (scripts/rebrand.py).
    desktop-src = {
      url = "path:./sources/desktop";
      flake = false;
    };
    # Quickshell той же ревизии, что собирает upstream (0.3.2.r7.g2b4501a);
    # поверх — патч загрузки плагинов (patches/quickshell-nixos-load.patch), без него
    # плагины из ~/.config/nixos/plugins не видят qs.Commons шелла.
    quickshell-src = {
      url = "github:quickshell-mirror/quickshell/2b4501a282689792b62e94f3fb30d8f512324fe6";
      flake = false;
    };
    # Zapret Hub (обход блокировок, ~/Work/zapret-hub): копия индекса git — scripts/sync-zapret-hub.sh.
    zapret-hub = {
      url = "path:./sources/zapret-hub";
      flake = false;
    };
    # Движок обоев (owed), в nixpkgs его нет.
    owe = {
      url = "github:omacom/owe";
      flake = false;
    };

    # Сторонние плагины бара и темы — локальные копии (~/Work/nixos-sources), без ссылок на чужие репозитории.
    plugin-advanced-clipboard = {
      url = "path:./sources/plugins/advanced-clipboard";
      flake = false;
    };
    plugin-rounded-corner-blur = {
      url = "path:./sources/plugins/rounded-corner-blur";
      flake = false;
    };
    plugin-tube = {
      url = "path:./sources/plugins/tube";
      flake = false;
    };
    plugin-hackernews = {
      url = "path:./sources/plugins/hackernews";
      flake = false;
    };
    plugin-jarvis = {
      url = "path:./sources/plugins/jarvis";
      flake = false;
    };
    plugin-vantage = {
      url = "path:./sources/plugins/vantage";
      flake = false;
    };
    plugin-glass-weather = {
      url = "path:./sources/plugins/glass-weather";
      flake = false;
    };
    plugin-resizeable = {
      url = "path:./sources/plugins/resizeable";
      flake = false;
    };
    plugin-window-switcher = {
      url = "path:./sources/plugins/window-switcher";
      flake = false;
    };
    plugin-lofi = {
      url = "path:./sources/plugins/lofi";
      flake = false;
    };
    plugin-sys-monitor = {
      url = "path:./sources/plugins/sys-monitor";
      flake = false;
    };
    plugin-whimsy = {
      url = "path:./sources/plugins/whimsy";
      flake = false;
    };

    # Темы.
    theme-drac = {
      url = "path:./sources/themes/drac";
      flake = false;
    };
    theme-neovoid = {
      url = "github:RiO7MAKK3R/omarchy-Neovoid-theme";
      flake = false;
    };
    theme-carchy = {
      url = "github:RiO7MAKK3R/omarchy-omacarchy-theme";
      flake = false;
    };
    theme-purple-moon = {
      url = "github:Grey-007/purple-moon";
      flake = false;
    };
    theme-rainynight = {
      url = "github:atif-1402/omarchy-rainynight-theme";
      flake = false;
    };
    theme-void = {
      url = "path:./sources/themes/void";
      flake = false;
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      home-manager,
      ...
    }@inputs0:
    let
      inputs = inputs0 // {
        desktop-src = inputs0.desktop-src // { outPath = builtins.path { path = inputs0.desktop-src.outPath; name = "source"; }; };
        plugin-advanced-clipboard = inputs0.plugin-advanced-clipboard // { outPath = builtins.path { path = inputs0.plugin-advanced-clipboard.outPath; name = "source"; }; };
        plugin-glass-weather = inputs0.plugin-glass-weather // { outPath = builtins.path { path = inputs0.plugin-glass-weather.outPath; name = "source"; }; };
        plugin-hackernews = inputs0.plugin-hackernews // { outPath = builtins.path { path = inputs0.plugin-hackernews.outPath; name = "source"; }; };
        plugin-jarvis = inputs0.plugin-jarvis // { outPath = builtins.path { path = inputs0.plugin-jarvis.outPath; name = "source"; }; };
        plugin-lofi = inputs0.plugin-lofi // { outPath = builtins.path { path = inputs0.plugin-lofi.outPath; name = "source"; }; };
        plugin-resizeable = inputs0.plugin-resizeable // { outPath = builtins.path { path = inputs0.plugin-resizeable.outPath; name = "source"; }; };
        plugin-rounded-corner-blur = inputs0.plugin-rounded-corner-blur // { outPath = builtins.path { path = inputs0.plugin-rounded-corner-blur.outPath; name = "source"; }; };
        plugin-sys-monitor = inputs0.plugin-sys-monitor // { outPath = builtins.path { path = inputs0.plugin-sys-monitor.outPath; name = "source"; }; };
        plugin-tube = inputs0.plugin-tube // { outPath = builtins.path { path = inputs0.plugin-tube.outPath; name = "source"; }; };
        plugin-vantage = inputs0.plugin-vantage // { outPath = builtins.path { path = inputs0.plugin-vantage.outPath; name = "source"; }; };
        plugin-whimsy = inputs0.plugin-whimsy // { outPath = builtins.path { path = inputs0.plugin-whimsy.outPath; name = "source"; }; };
        plugin-window-switcher = inputs0.plugin-window-switcher // { outPath = builtins.path { path = inputs0.plugin-window-switcher.outPath; name = "source"; }; };
        theme-drac = inputs0.theme-drac // { outPath = builtins.path { path = inputs0.theme-drac.outPath; name = "source"; }; };
        theme-void = inputs0.theme-void // { outPath = builtins.path { path = inputs0.theme-void.outPath; name = "source"; }; };
        zapret-hub = inputs0.zapret-hub // { outPath = builtins.path { path = inputs0.zapret-hub.outPath; name = "source"; }; };
      };
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      lib = nixpkgs.lib;

      mkHost =
        hostModule:
        lib.nixosSystem {
          inherit system;
          specialArgs = { inherit inputs self; };
          modules = [
            hostModule
            home-manager.nixosModules.home-manager
            self.nixosModules.desktop
            {
              home-manager.useGlobalPkgs = true;
              home-manager.useUserPackages = true;
              home-manager.backupFileExtension = "hm-bak";
              home-manager.extraSpecialArgs = { inherit inputs self; };
              home-manager.sharedModules = [ self.homeManagerModules.look ];
            }
          ];
        };

      # Раздаваемая система: та же ветка, что у пользователя (nixos-unstable = последние стабильные релизы
      # программ; на 26.05 Hyprland 0.55 не тянет конфиг под 0.57 — решение пользователя 24.11), без
      # личного; что ставить — choices.json (modules/nixos/share.nix).
      shareModules = [
            home-manager.nixosModules.home-manager
            self.nixosModules.desktop
            (import ./modules/nixos/share.nix { inherit inputs self; })
            {
              home-manager.useGlobalPkgs = true;
              home-manager.useUserPackages = true;
              home-manager.backupFileExtension = "hm-bak";
              home-manager.extraSpecialArgs = { inherit inputs self; };
              home-manager.sharedModules = [ self.homeManagerModules.look self.homeManagerModules.autostart ];
            }
          ];
      # «только оболочка» поверх своей NixOS (публичный репозиторий): home-manager + рабочий стол + shell.nix
      shellModules = [
        home-manager.nixosModules.home-manager
        self.nixosModules.desktop
        (import ./modules/nixos/shell.nix { inherit inputs self; })
      ];
      mkShellHost =
        modules:
        lib.nixosSystem {
          inherit system;
          specialArgs = { inherit inputs self; };
          modules = shellModules ++ modules;
        };
      mkShareHost =
        modules:
        lib.nixosSystem {
          inherit system;
          specialArgs = { inherit inputs self; };
          modules = shareModules ++ modules;
        };
    in
    {
      # для тестов и установщика: собрать хост share со своими choices/packages
      lib = { inherit mkShareHost shareModules mkShellHost; };
      # для своего флейка: imports = [ inputs.nixos-r-hypr-Next.nixosModules.shell ]; nextagg.shell = { enable = true; user = "…"; };
      nixosModules.shell = { imports = shellModules; };

      # Пакеты: рабочий стол, обои, плагины/темы и весь «вид» одной папкой.
      packages.${system} = import ./pkgs { inherit pkgs inputs self; };


      # Для друзей на NixOS: подключить эти два модуля (см. README).
      nixosModules.desktop = import ./modules/nixos/desktop.nix { inherit inputs self; };
      homeManagerModules.look = import ./modules/home/look.nix { inherit inputs self; };
      homeManagerModules.autostart = import ./modules/home/autostart.nix { inherit self; };

      nixosConfigurations = {
        # Раздаваемая система (ISO для друзей): без личного, choices.json.
        share = mkShareHost [ ./hosts/share ];
        # ISO для друзей: bash scripts/build-share-iso.sh (собирается с --impure, см. modules/nixos/share-iso.nix)
        share-iso = lib.nixosSystem {
          inherit system;
          modules = [ ./modules/nixos/share-iso.nix ];
        };
      };

      # nix run .#vm — работает и на других дистрибутивах: QEMU из Nix не видит системный Mesa
      # (/run/opengl-driver есть только на NixOS), поэтому подкладываем Mesa из nixpkgs.
      # Без окна: NEXTAGG_VM_HEADLESS=1 (картинка в VNC 127.0.0.1:5917).
      apps.${system} = {
        # оболочка на свою NixOS одной командой: nix run github:nextagg-zxc/nixos-r-hypr-Next#install
        install = {
          type = "app";
          program = toString (pkgs.writeShellScript "nixos-r-hypr-Next-install" ''
            export PATH=${lib.makeBinPath (with pkgs; [ coreutils hostname nixos-rebuild-ng gnugrep git ])}:$PATH
            exec ${pkgs.bash}/bin/bash ${./scripts/install-shell.sh} "$@"
          '');
        };


      };


      formatter.${system} = pkgs.nixfmt;
    };
}
