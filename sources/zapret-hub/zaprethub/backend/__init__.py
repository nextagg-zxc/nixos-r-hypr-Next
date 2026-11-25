from .. import config


def get_backend():
    if config.IS_WINDOWS:
        from .windows import WindowsBackend
        return WindowsBackend()
    from .linux import LinuxBackend
    return LinuxBackend()
