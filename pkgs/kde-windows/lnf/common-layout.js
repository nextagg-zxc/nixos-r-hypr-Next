// Общая часть раскладок «как Windows» (вставляется в начало layout.js каждой темы при сборке).
// Закреплённые значки — только установленные программы (applicationExists).
function pinned() {
    var want = ["firefox.desktop", "org.kde.dolphin.desktop", "org.nixos.Store.desktop", "steam.desktop",
                "discord.desktop", "spotify.desktop", "soundcloud.desktop", "zapret-hub.desktop"];
    var out = [];
    for (var i = 0; i < want.length; ++i) {
        if (applicationExists(want[i])) out.push("applications:" + want[i]);
    }
    return out.join(",");
}

function setupDesktops(wallpaper) {
    var ds = desktopsForActivity(currentActivity());
    for (var i = 0; i < ds.length; ++i) {
        var d = ds[i];
        d.wallpaperPlugin = "org.kde.image";
        d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
        d.writeConfig("Image", "file://" + wallpaper);
        // ярлыки на рабочем столе — столбиком слева сверху, как в Windows
        d.currentConfigGroup = ["General"];
        d.writeConfig("arrangement", 1);
        d.writeConfig("alignment", 0);
    }
}

function addStart(panel) {
    var kickoff = panel.addWidget("org.kde.plasma.kickoff");
    kickoff.currentConfigGroup = ["General"];
    kickoff.writeConfig("icon", "nix-snowflake-white");
    kickoff.currentConfigGroup = ["Shortcuts"];
    kickoff.writeConfig("global", "Alt+F1");
}

function addTasks(panel) {
    var tasks = panel.addWidget("org.kde.plasma.icontasks");
    tasks.currentConfigGroup = ["General"];
    tasks.writeConfig("launchers", pinned());
    tasks.writeConfig("groupingStrategy", 1);
}

function addTrayClockDesktop(panel) {
    panel.addWidget("org.kde.plasma.systemtray");
    var clock = panel.addWidget("org.kde.plasma.digitalclock");
    clock.currentConfigGroup = ["Appearance"];
    clock.writeConfig("showDate", true);
    clock.writeConfig("dateDisplayFormat", "BelowTime");
    clock.writeConfig("dateFormat", "shortDate");
    // «Свернуть всё» в правом углу (встроенный виджет Plasma 6)
    var sd = panel.addWidget("org.kde.plasma.showdesktop");
    sd.currentConfigGroup = ["General"];
    sd.writeConfig("minimizeAll", true);
}
