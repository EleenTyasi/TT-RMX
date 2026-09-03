"""
Fusion Engine package for Toontown Remix (TT-RMX).
"""

__version__ = "2.0.0"

from .diagnostics import (
    PANDA_ERROR_CODES,
    get_panda_error_info,
    parse_tracebacks,
    analyze_failure,
    package_bug_report,
)
from .launcher_gui import show_launcher_gui, FusionLauncherApp
from .dev_console import LiveSupervisor