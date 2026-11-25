# «Настройка системы» для раздаваемой системы: окно (GTK4/Adw) и root-помощник nixos-share-apply
# (pkexec, правило polkit на этот путь). Допустимые значения choices.json — из lib/choices.nix.
{
  lib,
  stdenvNoCC,
  python3,
  gtk4,
  libadwaita,
  gobject-introspection,
  wrapGAppsHook4,
  makeWrapper,
  sbctl,
  cryptsetup,
  systemd,
  util-linux,
  coreutils,
  papirus-icon-theme,
  libnotify,
}:
let
  py = python3.withPackages (p: [ p.pygobject3 ]);
  enums = builtins.toFile "share-choices-enums.json"
    (builtins.toJSON (import ../../lib/choices.nix { inherit lib; }).enums);
in
stdenvNoCC.mkDerivation {
  pname = "system-settings";
  version = "1.0";
  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [ ./system_settings ./nixos-share-apply.py ];
  };
  nativeBuildInputs = [ wrapGAppsHook4 gobject-introspection makeWrapper ];
  buildInputs = [ gtk4 libadwaita ];
  dontWrapGApps = true;
  installPhase = ''
    runHook preInstall
    mkdir -p $out/lib/system-settings $out/libexec $out/bin $out/share/system-settings \
      $out/share/applications $out/share/polkit-1/actions $out/share/icons/hicolor/scalable/apps
    cp -r system_settings $out/lib/system-settings/
    rm -rf $out/lib/system-settings/system_settings/__pycache__
    substituteInPlace $out/lib/system-settings/system_settings/ui.py --replace-fail '@helper@' "$out/libexec/nixos-share-apply"
    cp ${enums} $out/share/system-settings/enums.json
    install -m755 nixos-share-apply.py $out/libexec/.nixos-share-apply.py
    substituteInPlace $out/libexec/.nixos-share-apply.py --replace-fail '@enums@' "$out/share/system-settings/enums.json"
    cp ${papirus-icon-theme}/share/icons/Papirus/64x64/apps/systemsettings.svg \
      $out/share/icons/hicolor/scalable/apps/org.nixos.Settings.svg
    cat >$out/share/applications/org.nixos.Settings.desktop <<'DESKTOP'
    [Desktop Entry]
    Type=Application
    Name=Настройка системы
    Comment=Ядро, защита процессора, Secure Boot, Windows в меню загрузки, вид KDE
    Exec=nixos-settings
    Icon=org.nixos.Settings
    Categories=Settings;System;
    Keywords=settings;secure boot;tpm;kernel;настройки;ядро;
    Terminal=false
    DESKTOP
    sed -i 's/^    //' $out/share/applications/org.nixos.Settings.desktop
    cp ${papirus-icon-theme}/share/icons/Papirus/64x64/apps/system-software-update.svg \
      $out/share/icons/hicolor/scalable/apps/org.nixos.Update.svg
    cat >$out/share/applications/org.nixos.Update.desktop <<'DESKTOP'
    [Desktop Entry]
    Type=Application
    Name=Обновление системы
    Comment=Обновить систему и программы или откатить прежнюю версию
    Exec=nixos-settings --section update
    Icon=org.nixos.Update
    Categories=Settings;System;
    Keywords=update;upgrade;rollback;обновление;откат;
    Terminal=false
    DESKTOP
    sed -i 's/^    //' $out/share/applications/org.nixos.Update.desktop
    cat >$out/share/polkit-1/actions/org.nixos.settings.policy <<POLICY
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
     "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
    <policyconfig>
      <vendor>NixOS</vendor>
      <action id="org.nixos.settings.apply">
        <description>Change system settings</description>
        <description xml:lang="ru">Изменение настроек системы</description>
        <message>Authentication is required to change system settings</message>
        <message xml:lang="ru">Чтобы изменить настройки системы, нужен пароль</message>
        <icon_name>org.nixos.Settings</icon_name>
        <defaults>
          <allow_any>auth_admin</allow_any>
          <allow_inactive>auth_admin</allow_inactive>
          <allow_active>auth_admin_keep</allow_active>
        </defaults>
        <annotate key="org.freedesktop.policykit.exec.path">$out/libexec/nixos-share-apply</annotate>
      </action>
    </policyconfig>
    POLICY
    sed -i 's/^    //' $out/share/polkit-1/actions/org.nixos.settings.policy
    runHook postInstall
  '';
  postFixup = ''
    # pkexec сбрасывает PATH: всё нужное помощнику — в обёртке (nixos-rebuild — из системы)
    makeWrapper ${python3}/bin/python3 $out/libexec/nixos-share-apply \
      --add-flags "-I $out/libexec/.nixos-share-apply.py" \
      --prefix PATH : ${lib.makeBinPath [ sbctl cryptsetup systemd util-linux coreutils ]}:/run/current-system/sw/bin
    makeWrapper ${py}/bin/python3 $out/bin/nixos-settings "''${gappsWrapperArgs[@]}" \
      --prefix PYTHONPATH : $out/lib/system-settings --prefix PATH : ${lib.makeBinPath [ libnotify ]} \
      --add-flags "-m system_settings"
  '';
  meta = {
    description = "Настройка системы (раздаваемая система): ядро, защита, Secure Boot, TPM2, Windows, вид KDE";
    mainProgram = "nixos-settings";
  };
}
