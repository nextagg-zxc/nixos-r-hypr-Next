"""What the GUI needs from a platform. The read side (strategies, state,
results, lists) is plain files under config.DATA_DIR and is shared; changes
go through the platform subclass."""

import os
from dataclasses import dataclass, field

from .. import config, core


@dataclass
class Status:
    installed: bool = False
    running: bool = False
    autostart: bool = True
    strategy: str = "general"
    game_filter: str = "off"
    ipset: str = "none"
    versions: dict = field(default_factory=dict)
    conflicts: list = field(default_factory=list)


@dataclass
class Check:
    id: str
    level: str            # ok | warn | error
    title: str
    detail: str = ""
    fixable: bool = False
    fix_label: str = "Исправить"


# id -> (title, what to tell the user, button text)
CONFLICTS = {
    "flowseal_service": ("Работает служба zapret от Flowseal",
                         "Два обхода сразу мешают друг другу. Остановим и удалим службу Flowseal — "
                         "её заменяет эта программа.", "Удалить службу Flowseal"),
    "goodbyedpi": ("Работает GoodbyeDPI",
                   "GoodbyeDPI конфликтует с zapret. Остановим и отключим его автозапуск.", "Отключить GoodbyeDPI"),
    "stray_winws": ("Запущен другой winws.exe",
                    "Скорее всего открыт general.bat от Flowseal. Закроем его.", "Закрыть"),
    "windivert_stale": ("Висит драйвер WinDivert",
                        "Остался от прошлого запуска и может мешать. Уберём его.", "Убрать"),
    "zapret_gui": ("Работает старый zapret-gui",
                   "Старая программа и эта мешают друг другу. Остановим и отключим zapret-gui.", "Отключить zapret-gui"),
    "zapret_service": ("Работает служба zapret (bol-van)",
                       "Обычная установка zapret мешает этой программе. Остановим и отключим её.", "Отключить"),
}
BLOCKING_CONFLICTS = {"flowseal_service", "goodbyedpi", "stray_winws", "zapret_gui", "zapret_service"}


class ConflictError(RuntimeError):
    def __init__(self, ids):
        self.ids = ids
        super().__init__("Мешают другие программы обхода: " + ", ".join(CONFLICTS[i][0] for i in ids))


def best_strategy(results):
    """Strategy with the most passed checks, then the lowest ping; None if nothing passed."""
    best, key = None, None
    for name, r in results.items():
        if not r.get("total") or not r.get("ok"):
            continue
        k = (r["ok"] / r["total"], -(r.get("ping") or 9999))
        if key is None or k > key:
            best, key = name, k
    return best


class Backend:
    needs_admin_prompt = False   # Linux asks for a password per change (pkexec)

    # ------------------------------------------------------------ read side
    def is_installed(self):
        raise NotImplementedError

    def strategies(self):
        return core.list_strategies(config.BUILTIN_DIR, config.CUSTOM_DIR)

    def state(self):
        return core.load_state(config.STATE_FILE)

    def versions(self):
        return core.load_json(config.VERSIONS_FILE)

    def results(self):
        return core.load_json(config.RESULTS_FILE)

    def recommended(self):
        return best_strategy(self.results())

    def read_user_list(self, name):
        try:
            with open(os.path.join(config.LISTS_DIR, name), encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return ""
        return "" if text == core.USER_LISTS.get(name) else text

    def read_strategy(self, name):
        with open(core.strategy_path(name, config.BUILTIN_DIR, config.CUSTOM_DIR), encoding="utf-8") as f:
            return f.read()

    # ------------------------------------------------------------ changes (platform)
    def status(self):
        raise NotImplementedError

    def install(self, log):
        raise NotImplementedError

    def update(self, log):
        return self.install(log)

    def start(self, log):
        raise NotImplementedError

    def stop(self, log):
        raise NotImplementedError

    def set_autostart(self, on, log):
        raise NotImplementedError

    def set_state(self, changes, log):
        raise NotImplementedError

    def write_list(self, name, text, log):
        raise NotImplementedError

    def ipset_update(self, log):
        raise NotImplementedError

    def hosts(self, action, log):
        raise NotImplementedError

    def run_tests(self, names, on_event, cancel):
        raise NotImplementedError

    def diagnostics(self):
        raise NotImplementedError

    def fix(self, check_id, log):
        raise NotImplementedError

    def uninstall(self, log):
        raise NotImplementedError
