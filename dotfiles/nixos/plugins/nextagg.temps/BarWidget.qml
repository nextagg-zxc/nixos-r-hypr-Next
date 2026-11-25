import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Temps.js" as Temps

// Температуры CPU и видеокарты: hwmon (coretemp, k10temp, zenpower, xe, amdgpu, nouveau, nvme) и nvidia-smi;
// разбор — Temps.js. Нет датчика (VM, редкое железо) — значок с приглушённым «—°», чтобы бар не «проседал».
// Клик — btop.
BarWidget {
  id: root
  moduleName: "nextagg.temps"

  property var temps: ({})
  readonly property int hot: Number(setting("hot", 85))
  readonly property bool overheated: (temps.cpu || 0) >= hot || (temps.gpu || 0) >= hot

  // Как у sys-monitor слева: иконки — iconColor (белый), цифры — цвет текста бара.
  readonly property color iconColor: String(setting("iconColor", "#ffffff"))
  readonly property color valueColor: bar ? bar.barForeground : Color.foreground
  readonly property color hotColor: bar ? bar.urgent : Color.urgent
  implicitWidth: values.implicitWidth + Style.space(6) * 2
  implicitHeight: button.implicitHeight

  function tooltip() {
    var t = "CPU: " + Temps.label(temps.cpu) + "\nВидеокарта: " + Temps.label(temps.gpu)
    if (temps.vram !== undefined) t += "\nVRAM: " + Temps.label(temps.vram)
    if (temps.nvme !== undefined) t += "\nNVMe: " + Temps.label(temps.nvme)
    if (temps.cpu === undefined && temps.gpu === undefined) t += "\n(датчики температуры не найдены)"
    return t
  }

  // Кнопка — только клик и подсказка; подпись рисует Row ниже (двумя цветами).
  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: " "
    labelVisible: false
    fixedWidth: root.implicitWidth
    tooltipText: root.tooltip()
    onPressed: function(b) {
      if (root.bar) root.bar.run("nixos-launch-or-focus-tui btop")
    }
  }

  Row {
    id: values
    anchors.centerIn: parent
    spacing: Style.space(8)

    Repeater {
      model: [
        { icon: "\uf4bc", value: root.temps.cpu },
        { icon: "\udb82\udcae", value: root.temps.gpu }
      ]
      delegate: Row {
        required property var modelData
        opacity: modelData.value === undefined ? 0.45 : 1
        spacing: Style.space(4)
        anchors.verticalCenter: parent.verticalCenter
        readonly property bool hot: (modelData.value || 0) >= root.hot

        Text {
          text: modelData.icon
          font.family: Style.font.family
          font.pixelSize: Style.font.body
          color: parent.hot ? root.hotColor : root.iconColor
          anchors.verticalCenter: parent.verticalCenter
        }

        Text {
          textFormat: Text.PlainText
          text: Temps.label(modelData.value)
          font.family: Style.font.family
          font.pixelSize: Style.font.body
          color: parent.hot ? root.hotColor : root.valueColor
          anchors.verticalCenter: parent.verticalCenter
        }
      }
    }
  }

  Process {
    id: probe
    command: ["bash", "-c", "for h in /sys/class/hwmon/hwmon*; do n=$(cat $h/name); "
      + "for t in $h/temp*_input; do [ -e \"$t\" ] || continue; "
      + "l=$(cat ${t%_input}_label 2>/dev/null); echo \"$n|$l|$(cat $t)\"; done; done; "
      + "command -v nvidia-smi >/dev/null && t=$(nvidia-smi --query-gpu=temperature.gpu "
      + "--format=csv,noheader,nounits 2>/dev/null | head -1) && echo \"nvidia|gpu|$t\"; true"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.temps = Temps.parse(text)
    }
  }

  Timer {
    interval: Math.max(1, Number(root.setting("interval", 3))) * 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: probe.running = true
  }
}
