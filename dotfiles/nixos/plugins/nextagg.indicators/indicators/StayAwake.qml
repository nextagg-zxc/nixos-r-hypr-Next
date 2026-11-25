import QtQuick
import QtQuick.Effects
import qs.Commons
import qs.Ui

NaturalIndicator {
  id: root

  // Lit when on: accent colour (shell.json "activeColor" on the indicators
  // entry, default theme accent) plus a soft glow.
  // Sits half a pixel lower to line up with the bar text.
  transform: Translate { y: 0.5 }
  useActiveColor: true
  activeColor: root.indicatorHost && root.indicatorHost.setting
    ? root.indicatorHost.setting("activeColor", Color.accent) : Color.accent
  layer.enabled: root.effectiveActive
  layer.effect: MultiEffect {
    shadowEnabled: true
    shadowColor: root.activeColor
    shadowBlur: 0.8
    shadowHorizontalOffset: 0
    shadowVerticalOffset: 0
    shadowOpacity: 0.9
  }

  readonly property var idleService: bar?.shell?.firstPartyServiceFor("nixos.idle")

  active: idleService ? idleService.stayAwake : false
  activeText: "󰅶"
  inactiveText: "󰅶"
  activeTooltipText: "Allow Idle Lock & Screensaver"
  inactiveTooltipText: "Stay Awake"

  function toggle() {
    if (root.idleService) root.idleService.setIdleEnabled(root.active)
  }

  onPressed: function() { root.toggle() }
}
