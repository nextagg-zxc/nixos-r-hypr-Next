#!/usr/bin/env python3
"""Сетка приложений встроенного дока: звёздное небо (Starfield.qml из меню nextagg.menu) под
карточкой и затемнение остальных мониторов, пока сетка открыта (как у меню Win+B).

Патчится сам плагин nixos.dock при сборке пакета: копия плагина не годится — шелл даёт список
приложений (appLibrary) только встроенным плагинам и плагинам-меню.
  dock-patches.py <share/nixos/shell/plugins/dock> <Starfield.qml>
"""
import shutil
import sys

dock, starfield = sys.argv[1], sys.argv[2]
shutil.copyfile(starfield, dock + "/Starfield.qml")
p = dock + "/AppGrid.qml"
s = open(p, encoding="utf-8").read()
old = '''    BorderSurface {
      id: card
      width: root.cardWidth
      height: root.cardHeight
      anchors.centerIn: parent
      radius: Style.cornerRadius
      color: Commons.Color.menu.background
'''
new = '''    // nextagg: звёздное небо как в меню Win+B (Starfield.qml), под карточкой
    Starfield {
      x: card.x
      y: card.y
      width: card.width
      height: card.height
      opacity: card.opacity
      cornerRadius: Style.cornerRadius
      running: panel.shown
      fieldWidth: panel.width
      fieldHeight: panel.height
      fieldX: x
      fieldY: y
    }

    BorderSurface {
      id: card
      width: root.cardWidth
      height: root.cardHeight
      anchors.centerIn: parent
      radius: Style.cornerRadius
      color: "transparent"
'''


def patch(text, old, new):
    if text.count(old) != 1:
        sys.exit("dock-patches: AppGrid.qml изменился в апстриме — обновить scripts/dock-patches.py")
    return text.replace(old, new)


s = patch(s, old, new)

# затемнение остальных мониторов: отдельные окна-слои, клавиатуру не берут, клик закрывает сетку
s = patch(s, '''  OverlayWindow {
    id: panel
''', '''  // nextagg: пока сетка открыта, затемняются и остальные мониторы (тем же цветом)
  Variants {
    model: Quickshell.screens
    delegate: PanelWindow {
      required property var modelData
      screen: modelData
      visible: panel.shown && !!panel.targetScreen && panel.contentRevealed
               && modelData.name !== panel.targetScreen.name
      anchors { top: true; left: true; bottom: true; right: true }
      color: "transparent"
      exclusionMode: ExclusionMode.Ignore
      WlrLayershell.layer: WlrLayer.Overlay
      WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
      WlrLayershell.namespace: "nixos-dock-apps-dim"
      Rectangle {
        anchors.fill: parent
        color: Commons.Color.menu.scrim
        opacity: root.dragging ? 0 : 1
      }
      MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: root.close()
      }
    }
  }

  OverlayWindow {
    id: panel
''')
open(p, "w", encoding="utf-8").write(s)
print("dock-patches: ok")
