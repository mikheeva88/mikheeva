"""Точка входа: разбор параметров, создание окна и главный цикл."""

import tkinter as tk
from typing import Optional, Sequence

from emulator.config import parse_args
from emulator.gui import EmulatorApp


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Запустить графический эмулятор.

    Args:
        argv: параметры командной строки; если None, берутся из sys.argv.
    """
    config = parse_args(argv)
    root = tk.Tk()
    EmulatorApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
