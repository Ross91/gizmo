"""
Utility for connecting Maya Python environment to Pycharm for debugging.
"""
import sys
import logging

log = logging.getLogger("PyDebug")
log.setLevel(logging.DEBUG)


def connect() -> None:
    try:
        pydevd_egg = r"C:\Program Files\JetBrains\PyCharm 2023.2\debug-eggs\pydevd-pycharm.egg"
        if not pydevd_egg in sys.path:
            sys.path.append(pydevd_egg)

        import pydevd
        pydevd.stoptrace()
        pydevd.settrace('localhost', port=9001, stdoutToServer=True, stderrToServer=True, suspend=False)
    except Exception as e:
        # keep exception broad to catch everything.
        log.info('Failed to connect to pycharm!')
        log.debug(e)