from typing import Optional, Union

from rich.console import Console
from rich.progress import Progress, ProgressColumn
from rich.theme import Theme

# copy from pdm/termui.py

DEFAULT_THEME = {
    "primary": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    "req": "bold green",
}

_console = Console(highlight=False, theme=Theme(DEFAULT_THEME))


def is_legacy_windows(console: Optional[Console] = None):
    if console is None:
        console = _console
    return console.legacy_windows


class Emoji:
    if is_legacy_windows():
        SUCC = "v"
        FAIL = "x"
        LOCK = " "
        CONGRAT = " "
        POPPER = " "
        ELLIPSIS = "..."
        ARROW_SEPARATOR = ">"
    else:
        SUCC = ":heavy_check_mark:"
        FAIL = ":heavy_multiplication_x:"
        LOCK = ":lock:"
        POPPER = ":party_popper:"
        ELLIPSIS = "…"
        ARROW_SEPARATOR = "➤"


if is_legacy_windows():
    SPINNER = "line"

else:
    SPINNER = "dots"


class UI:
    
    def open_spinner(self, text: str):
        return _console.status(text, spinner=SPINNER, spinner_style="primary")

    def make_progress(
        self, *columns: Union[str, ProgressColumn], **kwargs
    ) -> Progress:
        return Progress(
            *columns,
            console=_console,
            **kwargs,
        )