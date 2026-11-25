import QtQuick
import Quickshell
import Quickshell.Io
import qs.Ui
import qs.Commons

// Флешки: значок в баре появляется, когда подключён USB-накопитель.
// Клик по строке — открыть в Files (смонтирует, если нужно), кнопка — извлечь.
Panel {
  id: root
  moduleName: "nextagg.usb-drives"
  ipcTarget: "nextagg.usb-drives"

  readonly property string helper: Qt.resolvedUrl("drives.sh").toString().replace("file://", "")

  property var drives: []
  // dev/disk -> "opening" | "ejecting"; сбрасывается, когда список обновился
  property var pending: ({})

  property int selectedIndex: 0
  property bool actionFocused: false
  property bool cursorActive: false

  readonly property color hoverFill: bar ? Style.hoverFillFor(bar.foreground, Color.accent) : "transparent"

  function refresh() { lister.running = true }

  function formatSize(bytes) {
    var units = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    var v = bytes, i = 0
    while (v >= 1000 && i < units.length - 1) { v /= 1024; i++ }
    return (v >= 100 || i === 0 ? Math.round(v) : v.toFixed(1)) + " " + units[i]
  }

  function driveName(d) {
    return d.label || d.model || "USB-накопитель"
  }

  function driveStatus(d) {
    if (d.ejected) return "Извлечена — можно вынимать"
    if (pending[d.disk] === "ejecting") return "Извлекается…"
    if (pending[d.dev] === "opening") return "Открывается…"
    var parts = [formatSize(d.size), d.fstype]
    parts.push(d.mount !== "" ? d.mount : "не смонтирована")
    return parts.join(" · ")
  }

  function setPending(key, action) {
    var next = Object.assign({}, pending)
    next[key] = action
    pending = next
    pendingTimeout.restart()
  }

  function openDrive(d) {
    if (!d || d.ejected) return
    setPending(d.dev, "opening")
    Quickshell.execDetached([helper, "open", d.dev])
    close()
  }

  function ejectDrive(d) {
    if (!d || d.ejected) return
    setPending(d.disk, "ejecting")
    Quickshell.execDetached([helper, "eject", d.disk])
  }

  function clampCursor() {
    if (selectedIndex > drives.length - 1) selectedIndex = Math.max(0, drives.length - 1)
  }

  onDrivesChanged: { pending = ({}); clampCursor(); if (drives.length === 0 && opened) close() }
  onOpenedChanged: if (opened) { refresh(); selectedIndex = 0; actionFocused = false; cursorActive = false }

  visible: drives.length > 0
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Process {
    id: lister
    command: [root.helper, "list"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try { root.drives = JSON.parse(text) } catch (e) {}
      }
    }
  }

  // Подключение/отключение устройств и монтирование — без опроса по таймеру.
  Process {
    running: true
    command: ["udevadm", "monitor", "--udev", "--subsystem-match=block"]
    stdout: SplitParser { onRead: function(line) { refreshDebounce.restart() } }
  }

  Process {
    running: true
    command: ["findmnt", "--poll", "-rn", "-o", "ACTION"]
    stdout: SplitParser { onRead: function(line) { refreshDebounce.restart() } }
  }

  Timer {
    id: refreshDebounce
    interval: 400
    onTriggered: root.refresh()
  }

  Timer {
    id: pendingTimeout
    interval: 20000
    onTriggered: root.pending = ({})
  }

  Component.onCompleted: refresh()

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "\uf287"
    tooltipText: root.drives.length === 1 ? root.driveName(root.drives[0]) : "Флешек: " + root.drives.length
    onPressed: function(b) {
      // ПКМ — сразу извлечь, если флешка одна
      if (b === Qt.RightButton && root.drives.length === 1) root.ejectDrive(root.drives[0])
      else root.toggle()
    }
  }

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(340))
    contentHeight: panel.fittedContentHeight(column.implicitHeight)

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onMoveRequested: function(dx, dy) {
        if (!root.cursorActive) { root.cursorActive = true; return }
        if (dy !== 0) {
          root.selectedIndex = Math.max(0, Math.min(root.drives.length - 1, root.selectedIndex + dy))
          root.actionFocused = false
        } else if (dx !== 0) {
          root.actionFocused = dx > 0
        }
      }
      onActivateRequested: {
        if (!root.cursorActive) return
        var d = root.drives[root.selectedIndex]
        if (root.actionFocused) root.ejectDrive(d)
        else root.openDrive(d)
      }
      onDeleteRequested: if (root.cursorActive) root.ejectDrive(root.drives[root.selectedIndex])
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }

      Column {
        id: column
        anchors.fill: parent
        spacing: Style.space(14)

        Item {
          width: parent.width
          implicitHeight: Math.max(heroIcon.implicitHeight, heroLabels.implicitHeight)

          Text {
            id: heroIcon
            textFormat: Text.PlainText
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            text: "\uf287"
            color: root.bar.foreground
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.display
          }

          Column {
            id: heroLabels
            anchors.left: heroIcon.right
            anchors.leftMargin: Style.space(14)
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: Style.space(2)

            Text {
              text: "Флешки"
              color: root.bar.foreground
              font.family: root.bar.fontFamily
              font.pixelSize: Style.font.title
              font.bold: true
            }

            Text {
              textFormat: Text.PlainText
              text: ("Подключено: " + root.drives.length).toUpperCase()
              color: Qt.darker(root.bar.foreground, 1.4)
              font.family: root.bar.fontFamily
              font.pixelSize: Style.font.caption
              font.bold: true
              font.letterSpacing: 1.2
            }
          }
        }

        PanelSeparator {
          foreground: root.bar.foreground
        }

        Column {
          id: driveList
          width: parent.width
          spacing: Style.space(10)

          Repeater {
            model: root.drives
            DriveRow {
              required property var modelData
              required property int index
              width: driveList.width
              drive: modelData
              rowIndex: index
            }
          }
        }
      }
    }
  }

  component DriveRow: CursorSurface {
    id: row
    required property var drive
    required property int rowIndex

    readonly property bool rowSelected: root.cursorActive && root.selectedIndex === rowIndex
    readonly property bool busy: root.pending[drive.disk] === "ejecting" || root.pending[drive.dev] === "opening"

    hasCursor: rowSelected && !root.actionFocused
    current: drive.mount !== ""
    foreground: root.bar.foreground
    fill: root.hoverFill
    currentFill: "transparent"
    implicitHeight: rowContent.implicitHeight + Style.spacing.rowPaddingX

    MouseArea {
      id: rowMouse
      anchors.fill: parent
      hoverEnabled: true
      cursorShape: row.drive.ejected ? Qt.ArrowCursor : Qt.PointingHandCursor
      onContainsMouseChanged: if (containsMouse) {
        root.cursorActive = true
        root.selectedIndex = row.rowIndex
        root.actionFocused = false
      }
      onClicked: root.openDrive(row.drive)
    }

    PanelToolTip {
      visible: rowMouse.containsMouse && !root.actionFocused && !row.drive.ejected
      text: "Открыть в Files"
      fontFamily: root.bar.fontFamily
    }

    Item {
      id: rowContent
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.verticalCenter: parent.verticalCenter
      anchors.leftMargin: Style.space(10)
      anchors.rightMargin: Style.space(10)
      implicitHeight: Math.max(driveIcon.implicitHeight, info.implicitHeight, ejectBtn.implicitHeight)

      Text {
        id: driveIcon
        textFormat: Text.PlainText
        text: "\uf287"
        color: root.bar.foreground
        opacity: row.drive.mount !== "" ? 1.0 : 0.6
        font.family: root.bar.fontFamily
        font.pixelSize: Style.font.heading
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
      }

      Column {
        id: info
        spacing: Style.space(1)
        anchors.left: driveIcon.right
        anchors.leftMargin: Style.space(10)
        anchors.right: ejectBtn.visible ? ejectBtn.left : parent.right
        anchors.rightMargin: ejectBtn.visible ? Style.space(8) : 0
        anchors.verticalCenter: parent.verticalCenter

        Text {
          textFormat: Text.PlainText
          text: root.driveName(row.drive)
          color: root.bar.foreground
          font.family: root.bar.fontFamily
          font.pixelSize: Style.font.body
          elide: Text.ElideRight
          width: parent.width
        }
        Text {
          textFormat: Text.PlainText
          text: root.driveStatus(row.drive)
          color: Qt.darker(root.bar.foreground, row.busy ? 1.0 : 1.5)
          font.family: root.bar.fontFamily
          font.pixelSize: Style.font.caption
          elide: Text.ElideMiddle
          width: parent.width
        }
      }

      PanelActionButton {
        id: ejectBtn
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        visible: !row.drive.ejected
        enabled: !row.busy
        iconText: "\uf052"
        tooltipText: "Извлечь"
        foreground: root.bar.foreground
        hoverColor: root.bar.foreground
        fontFamily: root.bar.fontFamily
        hasCursor: row.rowSelected && root.actionFocused
        onHovered: function(isHovered) {
          if (!isHovered) {
            if (rowMouse.containsMouse) root.actionFocused = false
            return
          }
          root.cursorActive = true
          root.selectedIndex = row.rowIndex
          root.actionFocused = true
        }
        onClicked: root.ejectDrive(row.drive)
      }
    }
  }
}
