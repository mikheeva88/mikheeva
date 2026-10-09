"""Точка входа: создание окна и запуск главного цикла."""

import tkinter as tk

from emulator.gui import EmulatorApp


def main() -> None:
    """Запустить графический эмулятор."""
    root = tk.Tk()
    EmulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
