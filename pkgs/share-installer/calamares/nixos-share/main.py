"""Шаг установки Calamares: раздаваемая NixOS (флейк в /etc/nixos, choices.json, nixos-install без интернета)."""
import importlib.util
import sys

import libcalamares

sys.path.insert(0, "@lib@")
from nixos_share import install  # noqa: E402


def _progress_parser():
    """Разбор прогресса nix (internal-json) — тот же, что в модуле nixos из calamares-nixos-extensions."""
    try:
        spec = importlib.util.spec_from_file_location(
            "upstream_nixos", "@upstream@/lib/calamares/modules/nixos/main.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.NixProgress()
    except Exception as e:  # noqa: BLE001
        libcalamares.utils.warning(f"прогресс nix недоступен: {e}")
        return None


def pretty_name():
    return "Установка NixOS"


def pretty_status_message():
    return "Установка NixOS…"


def run():
    gs = libcalamares.globalstorage
    answers = {k: gs.value(k) for k in gs.keys()}
    err = install.install(answers, gs.value("rootMountPoint"), gs.value("partitions") or [],
                          progress=libcalamares.job.setprogress, log=libcalamares.utils.debug,
                          progress_parser=_progress_parser())
    if err:
        return ("Установка не удалась", err)
    return None
