"""Графический интерфейс эмулятора на основе tkinter."""

import tkinter as tk
from tkinter import scrolledtext
from typing import Iterator, Optional

from emulator.commands import execute
from emulator.config import Config, format_debug
from emulator.script import ScriptError, iter_commands, load_script
from emulator.session import Session
from emulator.system_info import (
    format_prompt,
    format_title,
    get_hostname,
    get_username,
)
from emulator.vfs import VfsError, load_vfs

WINDOW_SIZE = "800x500"
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
ERROR_COLOR = "#f48771"
FONT = ("Courier New", 12)
ERROR_TAG = "error"
STEP_DELAY_MS = 300
WELCOME_TEXT = (
    "Эмулятор командной строки.\n"
    "Команды: ls, cd, echo, tac, exit, vfs-info, vfs-tree, vfs-show.\n"
)
SCRIPT_DONE_TEXT = "Стартовый скрипт выполнен.\n"


class EmulatorApp:
    """Окно эмулятора: область вывода и строка ввода (REPL)."""

    def __init__(self, root: tk.Tk, config: Optional[Config] = None) -> None:
        """Создать окно, задать заголовок по данным реальной ОС.

        Args:
            root: корневое окно tkinter.
            config: параметры запуска; если None, используются
                значения по умолчанию.
        """
        self.root = root
        self.config = config or Config()
        self.username = get_username()
        self.hostname = get_hostname()
        self.session = Session()
        self.root.title(format_title(self.username, self.hostname))
        self.root.geometry(WINDOW_SIZE)
        self._steps: Iterator[str] = iter(())
        self._build_widgets()
        self._print(WELCOME_TEXT)
        self._print(format_debug(self.config) + "\n")
        self._load_vfs()
        if self.config.script_path:
            self.root.after(STEP_DELAY_MS, self._start_script)

    def _prompt(self) -> str:
        """Вернуть приглашение с текущим каталогом."""
        return format_prompt(self.username, self.hostname, self.session.cwd)

    def _load_vfs(self) -> None:
        """Загрузить VFS из ZIP-архива в память, если задан --vfs."""
        path = self.config.vfs_path
        if path is None:
            return
        try:
            self.session.vfs = load_vfs(path)
        except VfsError as error:
            self._print(f"{error}\n", True)
            return
        stats = self.session.vfs.stats()
        self._print(
            f"VFS загружена в память: {path} "
            f"(каталогов: {stats.dirs}, файлов: {stats.files})\n"
        )

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
        self.prompt_label = tk.Label(
            bottom, text=self._prompt(), bg=BG_COLOR, fg=FG_COLOR, font=FONT,
        )
        self.prompt_label.pack(side=tk.LEFT)
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

    def _run_line(self, line: str) -> bool:
        """Выполнить строку и показать «диалог»: ввод и результат.

        Приглашение в выводе берётся до выполнения команды, после
        выполнения обновляется (текущий каталог мог измениться).

        Args:
            line: строка, введённая пользователем или взятая из скрипта.

        Returns:
            True, если эмулятор завершает работу (команда exit).
        """
        prompt = self._prompt()
        result = execute(line, self.session)
        self._print(f"{prompt} {line}\n")
        if result.output:
            self._print(result.output + "\n", result.is_error)
        self.prompt_label.config(text=self._prompt())
        if result.should_exit:
            self.root.destroy()
        return result.should_exit

    def _on_enter(self, _event: tk.Event) -> None:
        """Обработать нажатие Enter: выполнить введённую команду."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self._run_line(line)

    def _start_script(self) -> None:
        """Прочитать стартовый скрипт и начать его выполнение."""
        path = self.config.script_path
        try:
            lines = load_script(path)
        except ScriptError as error:
            self._print(f"{error}\n", True)
            return
        self._print(f"Выполнение стартового скрипта: {path}\n")
        self._steps = iter_commands(lines)
        self._next_step()

    def _next_step(self) -> None:
        """Выполнить очередную строку скрипта и запланировать следующую."""
        line = next(self._steps, None)
        if line is None:
            self._print(SCRIPT_DONE_TEXT)
            return
        if not self._run_line(line):
            self.root.after(STEP_DELAY_MS, self._next_step)
