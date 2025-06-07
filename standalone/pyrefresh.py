"""

"""
import sys
import logging
import importlib

log = logging.getLogger("Refresh")
log.setLevel(logging.DEBUG)


def package(name: str) -> None:
    """
    Reload package and package contents

    Args:
        name: name of package to reload
    """
    
    _remove = []
    for key in sys.modules.keys():
        if name in key:
            _remove.append(key)
    
    if not _remove:
        log.debug("No modules entry's to remove.")
        return

    for item in _remove:
        log.debug(f"Removing {item}")
        del sys.modules[item]

    try:
        importlib.import_module(name)
    except Exception as e:
        log.error(f'Failed to import package: {name}', e)
        