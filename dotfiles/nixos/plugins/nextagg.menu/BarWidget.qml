import QtQuick
import qs.Ui

BarWidget {
  id: root
  moduleName: "nixos.menu"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "\uf313"
    fontFamily: "nixos"
    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.run("xdg-terminal-exec")
      else root.bar.run("nixos-shell shell toggle nixos.menu '{\"menu\":\"root\"}'")
    }
  }
}
