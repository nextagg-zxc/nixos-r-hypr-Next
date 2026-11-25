import QtQuick
import QtQuick.Effects

// Звёздное небо в палитре системы (Catppuccin Mocha + лаванда #b4befe): сверху почти чёрное,
// книзу мягкий индиго с лавандовой дымкой; неподвижные звёзды (плотность w*h/4000, 1–2 px, яркость 0.5–1)
// и падающие звёзды под −45° с хвостом 300 px. Анимации идут, только пока running.
//
// Звёзды рисуются один раз на всё окно-подложку (fieldWidth × fieldHeight, обычно экран) с
// постоянным зерном, а небо показывает свой кусок (fieldX/fieldY — где небо в этом окне).
// Поэтому при смене подменю окно меняет размер, а звёзды стоят на месте и не перерисовываются.
// Скруглённые углы обрезаются маской.
Item {
  id: sky
  property bool running: false
  property real cornerRadius: 0
  property color skyTop: "#07070d"
  property color skyMiddle: "#121220"
  property color skyBottom: "#2a2c4f"
  // лавандовая дымка у нижнего края (мягкий свет, не сливается с подсветкой пунктов)
  property color haze: "#b4befe"
  property real hazeOpacity: 0.09
  property color star: "#ffffff"
  property real fieldWidth: 0
  property real fieldHeight: 0
  property real fieldX: 0
  property real fieldY: 0
  property int seed: 1337

  function rnd(a, b) { return a + Math.random() * (b - a) }

  Item {
    id: content
    anchors.fill: parent
    clip: true
    layer.enabled: true
    layer.effect: MultiEffect {
      maskEnabled: true
      maskSource: mask
      maskThresholdMin: 0.5
      maskSpreadAtMin: 1.0
    }

    Rectangle {
      anchors.fill: parent
      gradient: Gradient {
        GradientStop { position: 0; color: sky.skyTop }
        GradientStop { position: 0.45; color: sky.skyMiddle }
        GradientStop { position: 1; color: sky.skyBottom }
      }
    }

    Rectangle {
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.bottom: parent.bottom
      height: parent.height * 0.4
      gradient: Gradient {
        GradientStop { position: 0; color: "transparent" }
        GradientStop { position: 1; color: Qt.rgba(sky.haze.r, sky.haze.g, sky.haze.b, sky.hazeOpacity) }
      }
    }

    Canvas {
      id: stars
      x: -sky.fieldX
      y: -sky.fieldY
      width: Math.max(sky.width, sky.fieldWidth)
      height: Math.max(sky.height, sky.fieldHeight)
      property string painted: ""
      // перерисовка только при смене размера поля (экрана), не при смене размера окна
      readonly property string key: Math.round(width) + "x" + Math.round(height)
      onKeyChanged: requestPaint()
      onPaint: {
        var w = width, h = height
        if (w < 2 || h < 2 || painted === key) return
        painted = key
        // mulberry32: одинаковые звёзды при каждом открытии
        var a = sky.seed >>> 0
        function rand() {
          a = (a + 0x6D2B79F5) >>> 0
          var t = a
          t = Math.imul(t ^ (t >>> 15), t | 1)
          t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
          return ((t ^ (t >>> 14)) >>> 0) / 4294967296
        }
        var ctx = getContext("2d")
        ctx.reset()
        ctx.fillStyle = sky.star
        var count = Math.round((w * h) / 4000)
        for (var i = 0; i < count; i++) {
          var size = rand() < 0.5 ? 1 : 2
          ctx.globalAlpha = 0.5 + rand() * 0.5
          ctx.beginPath()
          ctx.arc(rand() * w, rand() * h, size / 2, 0, Math.PI * 2)
          ctx.fill()
        }
      }
    }

    // падающие: летят вниз-влево, хвост вверх-вправо, как @keyframes animate темы.
    // Таймер со случайной паузой запускает разовый пролёт; значения задаются до старта
    // (менять запущенную анимацию нельзя — она перезапускается и зацикливается).
    Repeater {
      model: 3
      delegate: Item {
        id: shoot
        width: 1
        height: 1
        opacity: 0
        rotation: -45
        transformOrigin: Item.TopLeft

        Rectangle {
          x: -2
          y: -2
          width: 4
          height: 4
          radius: 2
          color: sky.star
        }
        Rectangle {
          x: 0
          y: -0.5
          width: 300
          height: 1
          gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: sky.star }
            GradientStop { position: 1; color: "transparent" }
          }
        }

        function launch() {
          var sx, sy
          if (Math.random() < 0.5) { sx = sky.rnd(sky.width * 0.1, sky.width); sy = -4 }
          else { sx = sky.width + 4; sy = sky.rnd(0, sky.height * 0.5) }
          var t = Math.max(sky.width, sky.height) * 1.4 * 0.7071
          flyX.from = sx; flyX.to = sx - t
          flyY.from = sy; flyY.to = sy + t
          fly.start()
        }

        ParallelAnimation {
          id: fly
          NumberAnimation { id: flyX; target: shoot; property: "x"; duration: 3000 }
          NumberAnimation { id: flyY; target: shoot; property: "y"; duration: 3000 }
          SequentialAnimation {
            PropertyAction { target: shoot; property: "opacity"; value: 1 }
            PauseAnimation { duration: 2100 }
            NumberAnimation { target: shoot; property: "opacity"; to: 0; duration: 900 }
          }
          onFinished: {
            wait.interval = Math.round(sky.rnd(500, 7000))
            if (sky.running) wait.restart()
          }
        }

        Timer {
          id: wait
          interval: Math.round(sky.rnd(0, 7000))
          repeat: false
          running: sky.running
          onTriggered: shoot.launch()
        }

        Connections {
          target: sky
          function onRunningChanged() { if (!sky.running) { fly.stop(); shoot.opacity = 0 } }
        }
      }
    }
  }

  // маска скругления (не рисуется сама)
  Rectangle {
    id: mask
    anchors.fill: parent
    radius: sky.cornerRadius
    visible: false
    layer.enabled: true
    layer.smooth: true
  }
}
