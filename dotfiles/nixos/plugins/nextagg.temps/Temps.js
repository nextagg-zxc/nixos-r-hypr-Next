.pragma library

// Разбор датчиков для виджета температур. Строки «имя|метка|значение»: из hwmon значение в тысячных
// градуса, из nvidia-smi (имя «nvidia») — в градусах. Датчики узнаются по имени драйвера и метке, т.к.
// номера hwmonN меняются между загрузками. Порядок важности: у CPU Tctl > Tdie > Package, у GPU
// junction (горячая точка) > edge.
var CPU = [["coretemp", "Package id 0", 3], ["k10temp", "Tctl", 3], ["k10temp", "Tdie", 2],
           ["zenpower", "Tdie", 2], ["zenpower", "Tctl", 3]]
var GPU = [["xe", "pkg", 3], ["amdgpu", "junction", 3], ["amdgpu", "edge", 2], ["nouveau", "", 1],
           ["nvidia", "gpu", 3]]
var VRAM = [["xe", "vram", 3], ["amdgpu", "mem", 3]]

function rank(table, name, lbl) {
  for (var i = 0; i < table.length; i++)
    if (table[i][0] === name && table[i][1] === lbl) return table[i][2]
  return 0
}

function parse(text) {
  var out = {}, best = { cpu: 0, gpu: 0, vram: 0 }
  var lines = String(text || "").split("\n")
  for (var i = 0; i < lines.length; i++) {
    var f = lines[i].split("|")
    if (f.length < 3) continue
    var v = Number(f[2])
    if (!isFinite(v) || f[2] === "") continue
    if (f[0] !== "nvidia") v = v / 1000
    if (f[0] === "nvme" && f[1] === "Composite") { out.nvme = v; continue }
    var kinds = { cpu: CPU, gpu: GPU, vram: VRAM }
    for (var k in kinds) {
      var r = rank(kinds[k], f[0], f[1])
      if (r > best[k]) { best[k] = r; out[k] = v }
    }
  }
  return out
}

function label(value) {
  return value === undefined ? "—°" : Math.round(value) + "°"
}
