# Тест модуля в VM без сети: pkgs.testers.runNixOSTest.
# GitHub заменяет локальное «зеркало» (ZAPRETHUB_MIRROR) с маленьким поддельным релизом Flowseal.
{ pkgs, module }:
let
  # mirror — только Flowseal (zapret «не скачался» → nfqws из nixpkgs); mirrorFull — ещё и «свежий»
  # релиз zapret v99.1: его install_bin.sh кладёт nfq/nfqws (копия nfqws из nixpkgs).
  mirror = mkMirror false;
  mirrorFull = mkMirror true;
  mkMirror = withZapret: pkgs.runCommand "zapret-hub-test-mirror" {
    nativeBuildInputs = [ pkgs.python3 ];
    withZapret = if withZapret then "1" else "";
    nfqws = "${pkgs.zapret}/bin/nfqws";
  } ''
    python3 - <<'PY'
    import io, json, os, tarfile, zipfile
    out = os.environ["out"]
    def put(path, data):
        p = os.path.join(out, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data if isinstance(data, bytes) else data.encode())
    top = "zapret-discord-youtube-9.9.9"
    z = os.path.join(out, "gh/Flowseal/zapret-discord-youtube/releases/download/9.9.9", top + ".zip")
    os.makedirs(os.path.dirname(z), exist_ok=True)
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr(f"{top}/general.bat", '@echo off\nstart "zapret" /min "%BIN%winws.exe" --wf-tcp=80,443 ^\n'
                    '--filter-tcp=443 --hostlist="%LISTS%list-general.txt" --dpi-desync=fake\n')
        zf.writestr(f"{top}/bin/winws.exe", b"MZ")
        zf.writestr(f"{top}/bin/quic_initial_www_google_com.bin", b"\x00")
        zf.writestr(f"{top}/lists/list-general.txt", "discord.com\n")
        zf.writestr(f"{top}/lists/ipset-all.txt", "1.1.1.0/24\n2.2.2.0/24\n")
        zf.writestr(f"{top}/utils/targets.txt", 'YT = "https://www.youtube.com"\n')
    put("api/repos/Flowseal/zapret-discord-youtube/releases/latest", json.dumps({
        "tag_name": "9.9.9",
        "assets": [{"name": top + ".zip", "browser_download_url":
                    "https://github.com/Flowseal/zapret-discord-youtube/releases/download/9.9.9/" + top + ".zip"}]}))
    put("raw/Flowseal/zapret-discord-youtube/refs/heads/main/.service/hosts", "1.2.3.4 discord.media\n")
    if os.environ["withZapret"]:
        ztop = "zapret-v99.1"
        tgz = os.path.join(out, "gh/bol-van/zapret/releases/download/v99.1", ztop + ".tar.gz")
        os.makedirs(os.path.dirname(tgz), exist_ok=True)
        with tarfile.open(tgz, "w:gz") as t:
            def add(name, data, mode=0o644):
                ti = tarfile.TarInfo(f"{ztop}/{name}")
                ti.size, ti.mode = len(data), mode
                t.addfile(ti, io.BytesIO(data))
            add("install_bin.sh", b"#!/bin/sh\nset -e\nmkdir -p nfq\ncp binaries/linux-x86_64/nfqws nfq/nfqws\n"
                b"chmod 755 nfq/nfqws\n", 0o755)
            add("binaries/linux-x86_64/nfqws", open(os.environ["nfqws"], "rb").read(), 0o755)
        put("api/repos/bol-van/zapret/releases/latest", json.dumps({
            "tag_name": "v99.1",
            "assets": [{"name": ztop + ".tar.gz", "browser_download_url":
                        "https://github.com/bol-van/zapret/releases/download/v99.1/" + ztop + ".tar.gz"}]}))
    PY
  '';
in
pkgs.testers.runNixOSTest {
  name = "zapret-hub";
  nodes.machine = { ... }: {
    imports = [ module ];
    services.zapret-hub.enable = true;
    environment.systemPackages = [ pkgs.nftables pkgs.procps ];
  };
  testScript = { nodes, ... }:
    let
      pkg = nodes.machine.services.zapret-hub.package;
    in
    ''
      h = "${pkg}/libexec/zapret-hub-helper"
      env = "ZAPRETHUB_MIRROR=http://127.0.0.1:8000"

      def mirror(root="${mirror}"):
          machine.succeed("systemctl stop mirror.service || true")
          machine.succeed(f"systemd-run --unit mirror ${pkgs.python3}/bin/python3 -m http.server -d {root} 8000")
          machine.wait_for_open_port(8000)

      machine.wait_for_unit("multi-user.target")

      with subtest("polkit: помощник из правила = помощник окна"):
          policy = machine.succeed("cat /run/current-system/sw/share/polkit-1/actions/org.zaprethub.helper.policy")
          assert f">{h}<" in policy, policy
          wrapper = machine.succeed("cat ${pkg}/bin/zapret-hub")
          assert h in wrapper and "ZAPRETHUB_HELPER" in wrapper, wrapper
          machine.succeed("test -f /run/current-system/sw/share/applications/zapret-hub.desktop")

      with subtest("zapret не скачался — запасной nfqws из nixpkgs"):
          mirror()
          machine.succeed(f"{env} {h} install")
          machine.succeed("grep -q nixpkgs /opt/zapret-hub/versions.json")
          machine.succeed("test -d /opt/zapret-hub/strategies-builtin")
          machine.fail("test -e /opt/zapret-hub/zapret")
          machine.succeed(f"{h} service start")
          machine.succeed("pgrep -a nfqws | grep -q '/nix/store/.*-zapret-'")
          machine.succeed(f"{h} service stop")

      with subtest("свежий zapret скачан — служба запускает его nfqws"):
          mirror("${mirrorFull}")
          machine.succeed(f"{env} {h} install")
          machine.succeed("grep -q v99.1 /opt/zapret-hub/versions.json")
          machine.succeed("test -x /opt/zapret-hub/zapret/nfq/nfqws")
          machine.succeed(f"{h} service start")
          machine.succeed("systemctl is-active zapret-hub")
          machine.succeed("nft list table inet zapret_hub")
          machine.succeed("pgrep -a nfqws | grep -q '/opt/zapret-hub/zapret/nfq/nfqws'")
          machine.succeed("test -e /opt/zapret-hub/autostart")

      with subtest("автозапуск включён — служба после перезагрузки"):
          machine.shutdown()
          machine.start()
          machine.wait_for_unit("multi-user.target")
          machine.wait_until_succeeds("systemctl is-active zapret-hub", timeout=60)

      with subtest("автозапуск выключен — после перезагрузки служба не стартует"):
          machine.succeed(f"echo '{{\"autostart\": false}}' | {h} set-state")
          machine.succeed("test ! -e /opt/zapret-hub/autostart")
          machine.shutdown()
          machine.start()
          machine.wait_for_unit("multi-user.target")
          machine.sleep(5)
          machine.fail("systemctl is-active zapret-hub")

      with subtest("выключение: таблица убрана"):
          machine.succeed(f"{h} service start")
          machine.succeed(f"{h} service stop")
          machine.fail("systemctl is-active zapret-hub")
          machine.fail("nft list table inet zapret_hub")

      with subtest("hosts: блок переживает пересборку и убирается"):
          mirror()
          machine.succeed(f"{env} {h} hosts update")
          machine.succeed("grep -q '1.2.3.4 discord.media' /etc/hosts")
          machine.succeed("test -s /opt/zapret-hub/hosts.block")
          machine.succeed("/run/current-system/activate")
          machine.succeed("grep -q '1.2.3.4 discord.media' /etc/hosts")
          assert machine.succeed("grep -c 'zapret-hub >>>' /etc/hosts").strip() == "1"
          machine.succeed(f"{h} hosts remove")
          machine.succeed("/run/current-system/activate")
          machine.fail("grep -q zapret-hub /etc/hosts")
          machine.succeed("grep -q localhost /etc/hosts")
    '';
}
