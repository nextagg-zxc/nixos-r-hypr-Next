import QtQuick
import qs.Commons
import qs.Ui

// Ui/BarIndicator from NixOS 4.5 on top of NaturalIconButton, keeping the
// caption-sized glyph these indicators had before 4.5.
NaturalIconButton {
  id: root

  property string moduleName: ""
  property var settings: ({})
  property string activeText: ""
  property string inactiveText: activeText
  property string activeTooltipText: ""
  property string inactiveTooltipText: activeTooltipText
  property string indicatorBlock: "single"
  property var indicatorHost: null
  property var activeOverride: null
  property bool revealWhenInactive: true
  readonly property bool effectiveActive: activeOverride === null || activeOverride === undefined ? active : activeOverride === true
  readonly property bool belongsInBlock: indicatorBlock === "active" ? effectiveActive : (indicatorBlock === "inactive" ? !effectiveActive && revealWhenInactive : true)
  readonly property bool inactiveRevealed: !effectiveActive && revealWhenInactive && !!indicatorHost && indicatorHost.revealInactiveIndicators

  function extractData(raw) {
    return Util.parseModuleJson(raw)
  }

  function syncIndicatorOpacity() {
    root.opacity = !belongsInBlock ? 0 : (effectiveActive ? 1 : (inactiveRevealed ? 0.45 : 0))
  }

  Component.onCompleted: syncIndicatorOpacity()
  onActiveChanged: syncIndicatorOpacity()
  onEffectiveActiveChanged: syncIndicatorOpacity()
  onBarChanged: syncIndicatorOpacity()
  onBelongsInBlockChanged: syncIndicatorOpacity()
  onInactiveRevealedChanged: syncIndicatorOpacity()
  onIndicatorBlockChanged: syncIndicatorOpacity()

  visible: belongsInBlock && (text !== "" || keepSpace)
  text: effectiveActive ? activeText : inactiveText
  tooltipText: effectiveActive ? activeTooltipText : inactiveTooltipText
  keepSpace: true
  dimmed: !effectiveActive
  concealed: !effectiveActive && !inactiveRevealed
  interactive: belongsInBlock && (effectiveActive || indicatorBlock === "inactive" || inactiveRevealed)
  useActiveColor: false
  maintainIndicatorReveal: indicatorBlock === "inactive"
  revealHost: indicatorHost
  horizontalMargin: 5
  verticalPadding: 5
  fixedWidth: vertical ? -1 : Style.bar.statusSlot
  fixedHeight: vertical ? Style.bar.statusSlot : -1
  fontSize: Style.font.caption
}
