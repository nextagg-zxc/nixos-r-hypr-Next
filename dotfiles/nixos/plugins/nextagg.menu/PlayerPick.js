.pragma library

// Какой плеер показывает карточка меню Win+B.
// Настройка — однострочный файл ~/.config/nixos/media-player: "spotify" (по умолчанию) или
// "soundcloud". SoundCloud — окно Chromium из soundcloud-app; его MPRIS-имя
// org.mpris.MediaPlayer2.chromium.instance<PID>, а PID лежит в $XDG_RUNTIME_DIR/soundcloud-app.pid.
// Так меню берёт именно это окно, а не любой Chromium с видео.

function normalizeKind(text) {
  var kind = String(text === undefined || text === null ? "" : text).trim().toLowerCase()
  return kind === "soundcloud" ? "soundcloud" : "spotify"
}

function pickPlayer(players, kind, soundcloudPid) {
  var list = players || []
  if (normalizeKind(kind) === "soundcloud") {
    var pid = Math.floor(Number(soundcloudPid) || 0)
    if (pid <= 0) return null
    var want = "org.mpris.MediaPlayer2.chromium.instance" + pid
    for (var j = 0; j < list.length; j++) {
      var c = list[j]
      if (c && String(c.dbusName || "") === want) return c
    }
    return null
  }
  for (var i = 0; i < list.length; i++) {
    var p = list[i]
    if (!p) continue
    var id = (String(p.dbusName || "") + " " + String(p.identity || "") + " " + String(p.desktopEntry || "")).toLowerCase()
    if (id.indexOf("spotify") >= 0 && id.indexOf("playerctld") < 0) return p
  }
  return null
}
