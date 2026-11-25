# Разбор choices.json раздаваемой системы (что выбрал друг в установщике).
# normalize: сырой JSON → полный набор с значениями по умолчанию. Неизвестное поле или значение —
# ошибка вычисления с понятным текстом, а не молчаливое значение по умолчанию.
# Тесты: tests/share/choices.nix (nix build .#checks.x86_64-linux.share-choices).
{ lib }:
let
  fail = msg: throw "choices.json: ${msg}";
  oneOf = field: allowed: v:
    if builtins.elem v allowed then v
    else fail "${field} = ${builtins.toJSON v}, допустимо: ${lib.concatStringsSep ", " allowed}";
  bool = field: v: if builtins.isBool v then v else fail "${field} должно быть true/false, а не ${builtins.toJSON v}";
  str = field: v: if builtins.isString v then v else fail "${field} должно быть строкой";
  onlyKeys = field: allowed: attrs:
    let extra = lib.subtractLists allowed (builtins.attrNames attrs);
    in if extra == [ ] then attrs else fail "неизвестное поле ${field}${lib.concatStringsSep ", " extra}";

  enums = {
    desktop = [ "both" "hyprland" "kde" ];
    kdeLook = [ "win11" "win10" ];
    kernel = [ "cachyos" "zen" "linux" ];
    kernelBuild = [ "ready" "native" ];
    gpu = [ "mesa" "nvidia" "nvidia-legacy" ];
    player = [ "spotify" "soundcloud" ];
    extras = [ "gaming" "obs" "telegram" "autologin" "vr" ];
  };
  topKeys = [ "user" "hostname" "locale" "timezone" "keyboard" "desktop" "kdeLook" "kernel" "kernelBuild"
              "gpu" "player" "extras" "system" "boot" "hardware" ];
in
rec {
  inherit enums;

  normalize = raw0:
    let
      raw = onlyKeys "" topKeys raw0;
      u = onlyKeys "user." [ "name" "fullName" "passwordHash" ] (raw.user or { });
      name = str "user.name" (u.name or "user");
      s = onlyKeys "system." [ "mitigationsOff" "virtualization" "iommu" ] (raw.system or { });
      b = onlyKeys "boot." [ "secureBoot" "windows" ] (raw.boot or { });
      # пункт Windows в Limine: ESP по PARTUUID (только GUID — это попадает в конфиг загрузчика)
      win = w0:
        let
          w = onlyKeys "boot.windows[]." [ "name" "esp" ] w0;
          esp = lib.toLower (str "boot.windows[].esp" (w.esp or ""));
        in
        {
          name = str "boot.windows[].name" (w.name or "Windows");
          esp = if builtins.match "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" esp != null then esp
                else fail "boot.windows[].esp = ${builtins.toJSON (w.esp or null)}: нужен PARTUUID раздела EFI";
        };
      # железо, которое находит установщик: ноутбук, шины видеокарт (PRIME), btrfs, диски Windows
      h = onlyKeys "hardware." [ "laptop" "prime" "snapshots" "windowsDisks" ] (raw.hardware or { });
      bus = field: v:
        if v == null then null
        else if builtins.isString v && builtins.match "PCI:[0-9]{1,3}:[0-9]{1,2}:[0-9]" v != null then v
        else fail "${field} = ${builtins.toJSON v}: нужен адрес вида PCI:1:0:0";
      prime = p0:
        let p = onlyKeys "hardware.prime." [ "nvidiaBusId" "intelBusId" "amdgpuBusId" ] p0;
        in {
          nvidiaBusId = bus "hardware.prime.nvidiaBusId" (p.nvidiaBusId or null);
          intelBusId = bus "hardware.prime.intelBusId" (p.intelBusId or null);
          amdgpuBusId = bus "hardware.prime.amdgpuBusId" (p.amdgpuBusId or null);
        };
      winDisk = d0:
        let d = onlyKeys "hardware.windowsDisks[]." [ "uuid" "name" ] d0;
        in {
          uuid = if builtins.isString (d.uuid or null) && builtins.match "[0-9A-Fa-f]{16}" d.uuid != null then d.uuid
                 else fail "hardware.windowsDisks[].uuid = ${builtins.toJSON (d.uuid or null)}: нужен UUID раздела NTFS";
          name = let n = str "hardware.windowsDisks[].name" (d.name or "Windows"); in
            if builtins.match "[A-Za-z0-9_-]{1,32}" n != null then n
            else fail "hardware.windowsDisks[].name: латиница, цифры, _ и - (имя папки в /mnt)";
        };
      get = k: d: raw.${k} or d;
    in
    {
      user = {
        name = if builtins.match "[a-z_][a-z0-9_-]{0,31}" name != null then name
               else fail "user.name = ${builtins.toJSON name}: латиница в нижнем регистре, цифры, _ и -";
        fullName = str "user.fullName" (u.fullName or (if u ? name then name else "Пользователь"));
        passwordHash = u.passwordHash or null;
      };
      hostname = str "hostname" (get "hostname" "nixos");
      locale = str "locale" (get "locale" "ru_RU.UTF-8");
      timezone = str "timezone" (get "timezone" "Europe/Moscow");
      keyboard = map (str "keyboard[]") (get "keyboard" [ "us" "ru" ]);
      desktop = oneOf "desktop" enums.desktop (get "desktop" "both");
      kdeLook = oneOf "kdeLook" enums.kdeLook (get "kdeLook" "win11");
      kernel = oneOf "kernel" enums.kernel (get "kernel" "cachyos");
      kernelBuild = oneOf "kernelBuild" enums.kernelBuild (get "kernelBuild" "ready");
      gpu = oneOf "gpu" enums.gpu (get "gpu" "mesa");
      player = oneOf "player" enums.player (get "player" "spotify");
      extras = map (oneOf "extras[]" enums.extras) (get "extras" [ ]);
      system = {
        mitigationsOff = bool "system.mitigationsOff" (s.mitigationsOff or false);
        virtualization = bool "system.virtualization" (s.virtualization or true);
        iommu = bool "system.iommu" (s.iommu or true);
      };
      boot = {
        secureBoot = bool "boot.secureBoot" (b.secureBoot or false);
        windows = map win (b.windows or [ ]);
      };
      hardware = {
        laptop = bool "hardware.laptop" (h.laptop or false);
        prime = if (h.prime or null) == null then null else prime h.prime;
        snapshots = bool "hardware.snapshots" (h.snapshots or false);
        windowsDisks = map winDisk (h.windowsDisks or [ ]);
      };
    };

  # packages.json (Магазин): имена атрибутов nixpkgs, можно через точку (python3Packages.x).
  packageList = pkgs: names:
    map (n: lib.attrByPath (lib.splitString "." n)
      (throw "packages.json: нет пакета «${n}» в nixpkgs") pkgs) names;
}
