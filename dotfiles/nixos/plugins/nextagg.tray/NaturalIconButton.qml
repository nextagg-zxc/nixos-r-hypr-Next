import QtQuick
import qs.Commons
import qs.Ui

// A bar icon at its font size with native text rendering, as before NixOS 4.5.
// 4.5's BarIconButton scales every glyph to Style.bar.iconSize, which blows up
// small glyphs such as the tray chevron.
WidgetButton {
  id: root

  property real slotSize: Style.bar.iconSlot
  property real opticalSize: Style.bar.iconCanvas

  labelVisible: false
  hasVisualContent: text !== ""
  fontSize: Style.bar.iconFont
  fixedWidth: vertical ? -1 : slotSize
  fixedHeight: vertical ? slotSize : -1

  Item {
    anchors.centerIn: parent
    width: root.opticalSize
    height: root.opticalSize
    scale: root.pressScale

    OpticalGlyph {
      anchors.fill: parent
      text: root.text
      fontFamily: root.fontFamily
      fontSize: root.fontSize
      color: root.active && root.useActiveColor ? root.activeColor : root.foreground
      rotation: root.textRotation
    }
  }
}
