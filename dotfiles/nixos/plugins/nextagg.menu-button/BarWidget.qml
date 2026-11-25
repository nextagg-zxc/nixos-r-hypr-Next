import QtQuick
import qs.Ui
import qs.Commons

BarWidget {
  id: root
  moduleName: "nextagg.menu-button"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  // The NixOS glyph is not centered in its advance box; "iconOffsetX" nudges
  // it (in px, positive = left) so it sits in the middle of the segment.
  readonly property real iconOffsetX: Number(root.setting("iconOffsetX", 0))
  readonly property real iconScale: Number(root.setting("iconScale", 1))

  // "onAccent": true paints the logo in the bar background color, for an
  // accent-filled segment behind it.
  readonly property color iconColor: root.setting("onAccent", false) === true && root.bar
    ? root.bar.background : (root.bar ? root.bar.barForeground : "white")

  WidgetButton {
    id: button
    anchors.fill: parent
    anchors.leftMargin: -root.iconOffsetX
    anchors.rightMargin: root.iconOffsetX
    bar: root.bar
    text: ""
    fontFamily: "JetBrainsMono Nerd Font"
    fontSize: Style.font.body * root.iconScale
    // Single-glyph labels are scaled through a distance field; keep this one a text label.
    function isIconGlyph(value) { return false }
    centerFigures: false
    horizontalMargin: Number(root.setting("horizontalMargin", 7.5))
    foreground: root.iconColor
    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.run("xdg-terminal-exec")
      else root.bar.run("nixos-shell shell toggle nixos.menu '{\"menu\":\"root\"}'")
    }
  }
}
