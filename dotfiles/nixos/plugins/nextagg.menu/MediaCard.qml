import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris
import Quickshell.Services.Pipewire
import qs.Commons
import qs.Ui
import "PlayerPick.js" as PlayerPick

// Spotify в левой части меню Win+B: обложка,
// название, перемотка, перемешивание / назад / пауза / вперёд / повтор (выкл / плейлист /
// один трек), громкость. Цвета — тема Spotify StarryNight (белый, #ADB5BD, акцент #CBA6F7);
// фон-небо и рамку рисует общее окно (Menu.qml), справа — разделитель.
// Громкость — MPRIS Spotify; если плеер её не даёт — поток PipeWire (у SoundCloud — всегда поток). Колесо ±5 %.
// Мост Spicetify даёт обложки локальных треков через ~/.cache/nextagg/spotify-queue.json.
// Плеер выбирается файлом ~/.config/nixos/media-player: spotify (по умолчанию) или soundcloud —
// окно soundcloud-app (Chromium), его узнаём по PID из $XDG_RUNTIME_DIR/soundcloud-app.pid (PlayerPick.js).
BorderSurface {
  id: media

  required property var menu
  property bool shown: false
  // сколько места по высоте есть на экране — обложка ужимается, чтобы всё влезло
  property int maxHeight: 100000

  readonly property int pad: Style.space(22)
  readonly property int gap: Style.space(14)
  readonly property color fg: "#ffffff"
  readonly property color accent: "#cba6f7"
  readonly property color dim: "#adb5bd"
  readonly property color track: Qt.rgba(1, 1, 1, 0.18)
  readonly property string family: menu.fontFamily

  function glyph(cp) { return String.fromCodePoint(cp) }

  // ── какой плеер ──
  property string kind: "spotify"
  property int soundcloudPid: 0
  readonly property bool soundcloud: kind === "soundcloud"
  readonly property string playerName: soundcloud ? "SoundCloud" : "Spotify"
  readonly property var launchCommand: soundcloud ? ["uwsm-app", "--", "soundcloud-app"] : ["uwsm-app", "--", "spotify"]
  FileView {
    path: (Quickshell.env("XDG_CONFIG_HOME") || (Quickshell.env("HOME") + "/.config")) + "/nixos/media-player"
    watchChanges: true
    printErrors: false
    onLoaded: media.kind = PlayerPick.normalizeKind(text())
    onLoadFailed: media.kind = "spotify"
    onFileChanged: reload()
  }
  FileView {
    path: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/soundcloud-app.pid"
    watchChanges: true
    printErrors: false
    onLoaded: media.soundcloudPid = parseInt(String(text()).trim(), 10) || 0
    onLoadFailed: media.soundcloudPid = 0
    onFileChanged: reload()
  }

  // ── плеер и поток ──
  readonly property var players: Mpris.players ? Mpris.players.values : []
  readonly property var player: PlayerPick.pickPlayer(players, kind, soundcloudPid)
  // Поток PipeWire — запасной путь громкости, если плеер не даёт её через MPRIS.
  // SoundCloud: soundcloud-app называет поток «SoundCloud» (чужой Chromium так не называется).
  readonly property string streamName: soundcloud ? "soundcloud" : "spotify"
  // все потоки плеера (Chromium может открыть несколько) — громкость ставится на каждый
  readonly property var streams: {
    var out = []
    var ns = Pipewire.nodes ? Pipewire.nodes.values : []
    for (var i = 0; i < ns.length; i++) {
      var n = ns[i]
      if (n && n.isStream && String(n.name || "").toLowerCase() === streamName) out.push(n)
    }
    return out
  }
  readonly property var stream: streams.length > 0 ? streams[0] : null
  PwObjectTracker { objects: media.streams }

  // MPRIS Chromium объявляет громкость, но игнорирует запись (24.11) — у SoundCloud только поток.
  readonly property bool mprisVolume: !soundcloud && !!player && player.volumeSupported && player.canControl
  readonly property real volume: mprisVolume ? player.volume : (stream && stream.audio ? stream.audio.volume : 0)
  property real lastVolume: 0.5
  function setVolume(v) {
    v = Math.max(0, Math.min(1, v))
    if (v > 0.01) lastVolume = v
    if (mprisVolume) player.volume = v
    else for (var i = 0; i < streams.length; i++) if (streams[i] && streams[i].audio) streams[i].audio.volume = v
  }

  // MPRIS не шлёт позицию сам — опрашиваем, пока панель на экране.
  property real position: 0
  Timer {
    interval: 500
    repeat: true
    triggeredOnStart: true
    running: media.shown && !!media.player
    onTriggered: {
      if (!media.player) return
      media.player.positionChanged()
      media.position = media.player.position
    }
  }
  function fmt(sec) {
    if (!(sec > 0)) return "0:00"
    var s = Math.floor(sec)
    var m = Math.floor(s / 60)
    s = s % 60
    return m + ":" + (s < 10 ? "0" : "") + s
  }

  // Мост заранее сохраняет текущую и следующие обложки на диск.
  // Берём только обложку того же трека: снимок очереди может запаздывать за MPRIS.
  readonly property string artUrl: {
    var u = media.player ? String(media.player.trackArtUrl || "") : ""
    if (media.soundcloud) return u
    var c = media.queue ? media.queue.current : null
    var uri = c ? String(c.uri || "") : ""
    var metadata = media.player ? media.player.metadata : null
    var current = metadata ? String(metadata["xesam:url"] || "") : ""
    var local = uri.indexOf("spotify:local:") === 0
    var matches = uri && (current === uri || current.indexOf(uri.replace("spotify:track:", "https://open.spotify.com/track/")) === 0)
    if (c && (matches || (local && !u && String(c.title || "") === String(media.player ? media.player.trackTitle || "" : "")))) {
      var cached = String(c.image || "")
      if (cached) return cached
    }
    return u
  }

  // ── очередь из расширения Spicetify ──
  property var queue: ({ connected: false, current: null, next: [], prev: [], liked: false })
  FileView {
    path: (Quickshell.env("XDG_CACHE_HOME") || (Quickshell.env("HOME") + "/.cache")) + "/nextagg/spotify-queue.json"
    watchChanges: true
    printErrors: false
    onLoaded: {
      try {
        var q = JSON.parse(text())
        if (q && typeof q === "object") media.queue = q
      } catch (e) {}
    }
    onFileChanged: reload()
  }
  color: "transparent"
  radius: menu.cornerRadius
  implicitHeight: content.implicitHeight + pad * 2

  // Клики по панели не должны закрывать меню (под ней — затемнение с cancel()).
  MouseArea {
    anchors.fill: parent
    acceptedButtons: Qt.AllButtons
    onClicked: {}
    onWheel: function(wheel) {
      media.setVolume(media.volume + (wheel.angleDelta.y > 0 ? 0.05 : -0.05))
    }
  }

  component Glyph: Text {
    textFormat: Text.PlainText
    font.family: media.family
    color: media.fg
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
  }

  component IconButton: Item {
    id: btn
    property int cp: 0
    property url iconSource: ""
    property int size: Style.space(54)
    property real iconRatio: 0.5
    property bool active: false
    property bool dot: false
    property bool enabledButton: true
    signal activated()
    width: size
    height: size
    Glyph {
      visible: !btn.iconSource.toString()
      anchors.centerIn: parent
      width: btn.size
      height: btn.size
      text: media.glyph(btn.cp)
      color: media.fg
      opacity: btn.enabledButton ? 1 : 0.35
      font.pixelSize: Math.round(btn.size * btn.iconRatio)
      scale: hover.containsMouse && btn.enabledButton ? 1.08 : 1
    }
    Image {
      anchors.centerIn: parent
      visible: !!btn.iconSource.toString()
      source: btn.iconSource
      width: Math.round(btn.size * btn.iconRatio)
      height: width
      sourceSize.width: width * Screen.devicePixelRatio
      sourceSize.height: height * Screen.devicePixelRatio
      opacity: btn.enabledButton ? 1 : 0.35
      scale: hover.containsMouse && btn.enabledButton ? 1.08 : 1
    }
    // точка под активной кнопкой, как в Spotify
    Rectangle {
      visible: btn.dot
      width: Math.max(4, Math.round(btn.size * 0.09))
      height: width
      radius: width / 2
      color: media.dim
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.bottom: parent.bottom
      anchors.bottomMargin: Math.round(btn.size * 0.08)
    }
    MouseArea {
      id: hover
      anchors.fill: parent
      hoverEnabled: true
      cursorShape: btn.enabledButton ? Qt.PointingHandCursor : Qt.ArrowCursor
      onClicked: if (btn.enabledButton) btn.activated()
    }
  }

  // всё, кроме обложки, — чтобы посчитать, сколько ей остаётся по высоте
  readonly property int restHeight: titles.height + progress.height + controls.height
                                    + volumeRow.height + content.spacing * 4 + pad * 2
  readonly property int artSize: Math.max(Style.space(120), Math.min(content.width, maxHeight - restHeight))

  Column {
    id: content
    x: media.pad
    y: media.pad
    width: media.width - media.pad * 2
    spacing: media.gap

    // круглая обложка со свечением (как в теме StarryNight)
    Item {
      id: artArea
      width: content.width
      height: media.artSize

      // круглая обложка
      Item {
        id: disc
        readonly property int size: Math.max(Style.space(80), Math.min(artArea.height, artArea.width) - Style.space(10))
        width: size
        height: size
        anchors.centerIn: parent

        // мягкое белое свечение по краю
        Rectangle {
          anchors.centerIn: parent
          width: parent.width + Style.space(10)
          height: width
          radius: width / 2
          color: "#ffffff"
          opacity: 0.85
          layer.enabled: true
          layer.effect: MultiEffect { blurEnabled: true; blur: 1.0; blurMax: 32; autoPaddingEnabled: true }
        }
        Rectangle {
          anchors.centerIn: parent
          width: parent.width + Style.space(4)
          height: width
          radius: width / 2
          color: "#ffffff"
        }
        Rectangle {
          anchors.fill: parent
          radius: width / 2
          color: "#1e1e2e"
          Glyph {
            anchors.centerIn: parent
            visible: art.status !== Image.Ready
            text: media.glyph(0xF075A)
            color: media.dim
            font.pixelSize: Math.round(parent.width * 0.3)
          }
        }
        Image {
          id: art
          anchors.fill: parent
          source: media.artUrl
          fillMode: Image.PreserveAspectCrop
          asynchronous: true
          cache: true
          // Fixed decoding size avoids reloading the same cover during menu animations.
          sourceSize.width: 640
          sourceSize.height: 640
          visible: false
          layer.enabled: true
        }
        Rectangle {
          id: discMask
          anchors.fill: parent
          radius: width / 2
          visible: false
          layer.enabled: true
          layer.smooth: true
        }
        MultiEffect {
          anchors.fill: parent
          source: art
          visible: art.status === Image.Ready
          maskEnabled: true
          maskSource: discMask
          maskThresholdMin: 0.5
          maskSpreadAtMin: 1.0
        }
      }

    }

    // название и исполнитель
    Column {
      id: titles
      width: content.width
      spacing: Style.space(4)
      Item {
        width: parent.width
        height: Math.max(titleText.implicitHeight, Style.space(34))
        Row {
          anchors.horizontalCenter: parent.horizontalCenter
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(12)
          Glyph {
            id: titleText
            anchors.verticalCenter: parent.verticalCenter
            width: Math.min(implicitWidth, titles.width)
            elide: Text.ElideRight
            font.pixelSize: Math.round(Style.font.heading * 1.5)
            font.bold: true
            text: media.player ? (String(media.player.trackTitle || "") || "—") : (media.playerName + " не запущен")
          }
        }
      }
      Glyph {
        visible: !media.player
        width: parent.width
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
        font.pixelSize: Math.round(Style.font.body * 1.35)
        color: media.dim
        text: "Нажмите ▶, чтобы открыть"
      }
    }

    // перемотка
    Column {
      id: progress
      width: content.width
      spacing: Style.space(6)
      opacity: media.player ? 1 : 0.35
      Item {
        width: parent.width
        height: Style.space(18)
        Rectangle {
          anchors.verticalCenter: parent.verticalCenter
          width: parent.width
          height: Style.space(6)
          radius: height / 2
          color: media.track
          Rectangle {
            width: media.player && media.player.length > 0
                   ? parent.width * Math.min(1, media.position / media.player.length) : 0
            height: parent.height
            radius: height / 2
            color: media.fg
          }
        }
        MouseArea {
          anchors.fill: parent
          enabled: !!media.player && media.player.canSeek && media.player.length > 0
          cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
          onClicked: function(mouse) {
            var t = Math.max(0, Math.min(1, mouse.x / width)) * media.player.length
            media.player.position = t
            media.position = t
          }
        }
      }
      Item {
        width: parent.width
        height: Math.round(Style.font.caption * 1.3) + Style.space(2)
        Glyph { anchors.left: parent.left; font.pixelSize: Math.round(Style.font.caption * 1.3); color: media.dim; text: media.fmt(media.position) }
        Glyph {
          anchors.right: parent.right
          font.pixelSize: Math.round(Style.font.caption * 1.3)
          color: media.dim
          text: media.fmt(media.player ? media.player.length : 0)
        }
      }
    }

    // кнопки
    Item {
      id: controls
      width: content.width
      height: Style.space(72)
      Row {
        anchors.centerIn: parent
        height: parent.height
        spacing: Style.space(18)
        IconButton {
          anchors.verticalCenter: parent.verticalCenter
          size: Style.space(60)
          iconRatio: 0.46
          iconSource: Qt.resolvedUrl("icons/shuffle.svg")
          enabledButton: !!media.player && media.player.shuffleSupported
          active: !!media.player && media.player.shuffle
          dot: active
          onActivated: media.player.shuffle = !media.player.shuffle
        }
        IconButton {
          anchors.verticalCenter: parent.verticalCenter
          size: Style.space(60)
          iconRatio: 0.46
          iconSource: Qt.resolvedUrl("icons/previous.svg")
          enabledButton: !!media.player && media.player.canGoPrevious
          onActivated: media.player.previous()
        }
        Rectangle {
          objectName: "playButton"
          anchors.verticalCenter: parent.verticalCenter
          width: Style.space(62)
          height: width
          radius: width / 2
          color: media.fg
          Image {
            anchors.centerIn: parent
            source: Qt.resolvedUrl(media.player && media.player.isPlaying ? "icons/pause.svg" : "icons/play.svg")
            width: Style.space(28)
            height: width
            sourceSize.width: width * Screen.devicePixelRatio
            sourceSize.height: height * Screen.devicePixelRatio
          }
          MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: {
              if (media.player) media.player.togglePlaying()
              else Quickshell.execDetached(media.launchCommand)
            }
          }
        }
        IconButton {
          anchors.verticalCenter: parent.verticalCenter
          size: Style.space(60)
          iconRatio: 0.46
          iconSource: Qt.resolvedUrl("icons/next.svg")
          enabledButton: !!media.player && media.player.canGoNext
          onActivated: media.player.next()
        }
        // повтор: выкл → плейлист → один трек (значок с «1»), как в Spotify
        IconButton {
          anchors.verticalCenter: parent.verticalCenter
          size: Style.space(60)
          iconRatio: 0.46
          readonly property int loop: media.player ? media.player.loopState : MprisLoopState.None
          iconSource: Qt.resolvedUrl(loop === MprisLoopState.Track ? "icons/repeat-one.svg" : "icons/repeat.svg")
          enabledButton: !!media.player && media.player.loopSupported
          active: loop !== MprisLoopState.None
          dot: active
          onActivated: media.player.loopState = loop === MprisLoopState.None
                       ? MprisLoopState.Playlist
                       : (loop === MprisLoopState.Playlist ? MprisLoopState.Track : MprisLoopState.None)
        }
      }
    }

    // громкость
    Row {
      id: volumeRow
      width: content.width
      spacing: Style.space(12)
      opacity: (media.mprisVolume || !!(media.stream && media.stream.audio)) ? 1 : 0.35
      IconButton {
        id: muteButton
        anchors.verticalCenter: parent.verticalCenter
        size: Style.space(44)
        cp: media.volume <= 0.01 ? 0xF0581 : (media.volume < 0.5 ? 0xF057F : 0xF057E)
        onActivated: media.setVolume(media.volume > 0.01 ? 0 : media.lastVolume)
      }
      Item {
        id: slider
        objectName: "volumeSlider"
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width - muteButton.width - percent.width - parent.spacing * 2
        height: Style.space(28)
        Rectangle {
          anchors.verticalCenter: parent.verticalCenter
          width: parent.width
          height: Style.space(6)
          radius: height / 2
          color: media.track
          Rectangle {
            width: parent.width * Math.max(0, Math.min(1, media.volume))
            height: parent.height
            radius: height / 2
            color: media.fg
          }
        }
        Rectangle {
          width: Style.space(18)
          height: width
          radius: width / 2
          color: media.fg
          anchors.verticalCenter: parent.verticalCenter
          x: (slider.width - width) * Math.max(0, Math.min(1, media.volume))
        }
        MouseArea {
          anchors.fill: parent
          cursorShape: Qt.PointingHandCursor
          function apply(mx) { media.setVolume(mx / width) }
          onPressed: function(mouse) { apply(mouse.x) }
          onPositionChanged: function(mouse) { if (pressed) apply(mouse.x) }
        }
      }
      Glyph {
        id: percent
        anchors.verticalCenter: parent.verticalCenter
        width: Style.space(52)
        font.pixelSize: Math.round(Style.font.body * 1.2)
        color: media.dim
        text: Math.round(media.volume * 100) + "%"
      }
    }
  }

  // разделитель с меню справа
  Rectangle {
    anchors.right: parent.right
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    anchors.topMargin: media.pad
    anchors.bottomMargin: media.pad
    width: Math.max(1, Style.space(1))
    color: media.menu.border
  }
}
