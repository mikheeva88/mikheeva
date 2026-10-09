"""Графический интерфейс эмулятора на основе tkinter."""

import tkinter as tk
from tkinter import scrolledtext

from emulator.commands import execute
from emulator.system_info import (
    format_prompt,
    format_title,
    get_hostname,
    get_username,
)

WINDOW_SIZE = "800x500"
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
ERROR_COLOR = "#f48771"
FONT = ("Courier New", 12)
ERROR_TAG = "error"
WELCOME_TEXT = (
    "Эмулятор командной строки. Доступные команды: ls, cd, exit.\n"
)


class EmulatorApp:
    """Окно эмулятора: область вывода и строка ввода (REPL)."""

    def __init__(self, root: tk.Tk) -> None:
        """Создать окно, задать заголовок по данным реальной ОС.

        Args:
            root: корневое окно tkinter.
        """
        self.root = root
        username = get_username()
        hostname = get_hostname()
        self.prompt = format_prompt(username, hostname)
        self.root.title(format_title(username, hostname))
        self.root.geometry(WINDOW_SIZE)
        self._build_widgets()
        self._print(WELCOME_TEXT)

    def _build_widgets(self) -> None:
        """Создать область вывода, приглашение и поле ввода."""
        self.output = scrolledtext.ScrolledText(
            self.root, bg=BG_COLOR, fg=FG_COLOR, font=FONT,
            state=tk.DISABLED, wrap=tk.WORD,
        )
        self.output.tag_config(ERROR_TAG, foreground=ERROR_COLOR)
        self.output.pack(fill=tk.BOTH, expand=True)
        bottom = tk.Frame(self.root, bg=BG_COLOR)
        bottom.pack(fill=tk.X)
        tk.Label(
            bottom, text=self.prompt, bg=BG_COLOR, fg=FG_COLOR, font=FONT,
        ).pack(side=tk.LEFT)
        self.entry = tk.Entry(
            bottom, bg=BG_COLOR, fg=FG_COLOR, font=FONT,
            insertbackground=FG_COLOR, relief=tk.FLAT,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.focus_set()

    def _print(self, text: str, is_error: bool = False) -> None:
        """Добавить текст в конец области вывода.

        Args:
            text: добавляемый текст.
            is_error: если True, текст выделяется цветом ошибки.
        """
        tags = (ERROR_TAG,) if is_error else ()
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text, tags)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def _on_enter(self, _event: tk.Event) -> None:
        """Обработать нажатие Enter: выполнить введённую команду."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self._print(f"{self.prompt} {line}\n")
        result = execute(line)
        if result.output:
            self._print(result.output + "\n", result.is_error)
        if result.should_exit:
            self.root.destroy()
