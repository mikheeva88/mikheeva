"""Эмулятор командной строки UNIX-подобной ОС (вариант 18)."""

import argparse
import base64
import getpass
import shlex
import socket
import tkinter as tk
import zipfile
import zlib
from tkinter import scrolledtext
from typing import (
    Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple, Union,
)

ROOT = "/"
UNKNOWN = "unknown"
NOT_SET = "(не задан)"
NOT_FOUND = "нет такого файла или каталога"
TOO_MANY = "слишком много аргументов"
BINARY_TEXT = "(двоичный файл, base64)"
NUL = "\x00"
NEWLINE = b"\n"
COMMENT = "#"
WINDOW_SIZE = "800x500"
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
ERROR_COLOR = "#f48771"
FONT = ("Courier New", 12)
ERROR_TAG = "error"
STEP_DELAY_MS = 300
WELCOME_TEXT = "Эмулятор командной строки. Команды: ls, cd, echo, tac, exit.\n"
LOAD_ERRORS = (
    OSError,
    zipfile.BadZipFile,
    RuntimeError,
    NotImplementedError,
    EOFError,
    zlib.error,
)


class VfsError(Exception):
    """Ошибка загрузки VFS."""


class ScriptError(Exception):
    """Ошибка чтения стартового скрипта."""


class CommandError(Exception):
    """Ошибка команды (текст показывается пользователю)."""


class Result(NamedTuple):
    """Результат команды: текст, признак ошибки, признак выхода."""

    output: str
    is_error: bool = False
    should_exit: bool = False


def split_path(path: str) -> List[str]:
    """Разбить путь по «/», отбросив пустые части и «.»."""
    return [part for part in path.split("/") if part and part != "."]


def add_entry(root: dict, name: str, data: bytes, is_dir: bool) -> None:
    """Добавить запись ZIP-архива в дерево VFS (словари и байты)."""
    parts = split_path(name)
    if ".." in parts:
        raise VfsError(f"недопустимый путь в архиве: '{name}'")
    if not parts:
        return
    folder = root
    for part in parts if is_dir else parts[:-1]:
        folder = folder.setdefault(part, {})
        if not isinstance(folder, dict):
            raise VfsError(f"конфликт имён в записи '{name}'")
    if not is_dir and parts[-1] in folder:
        raise VfsError(f"повторяющаяся запись '{name}'")
    if not is_dir:
        folder[parts[-1]] = data


def load_vfs(path: str) -> dict:
    """Загрузить ZIP-архив в память: каталог это dict, файл это bytes."""
    root: dict = {}
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                data = b"" if info.is_dir() else archive.read(info)
                add_entry(root, info.filename, data, info.is_dir())
    except LOAD_ERRORS as error:
        raise VfsError(f"не удалось загрузить VFS '{path}': {error}") from error
    return root


def reverse_lines(data: bytes) -> bytes:
    """Записать строки данных в обратном порядке."""
    lines = data.split(NEWLINE)
    if lines[-1] == b"":
        lines.pop()
    lines.reverse()
    return NEWLINE.join(lines)


def is_text(data: bytes) -> bool:
    """Проверить, что данные это текст UTF-8 без нулевых байтов."""
    try:
        return NUL not in data.decode("utf-8")
    except UnicodeDecodeError:
        return False


def format_content(data: bytes) -> str:
    """Текст выводится как есть, двоичные данные в base64."""
    if is_text(data):
        return data.decode("utf-8").replace("\r\n", "\n").rstrip("\n")
    encoded = base64.encodebytes(data).decode("ascii").rstrip("\n")
    return f"{BINARY_TEXT}\n{encoded}"


class Shell:
    """Оболочка: VFS в памяти, текущий каталог и команды."""

    def __init__(self, vfs: dict) -> None:
        """Создать оболочку с заданной VFS, текущий каталог корень."""
        self.vfs = vfs
        self.cwd = ROOT
        self.commands: Dict[str, Callable[[List[str]], Result]] = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "echo": self.cmd_echo,
            "tac": self.cmd_tac,
            "exit": self.cmd_exit,
        }

    def resolve(self, path: str) -> List[str]:
        """Превратить путь в список частей от корня (учёт «..»)."""
        parts = [] if path.startswith(ROOT) else split_path(self.cwd)
        for part in split_path(path):
            if part != "..":
                parts.append(part)
            elif parts:
                parts.pop()
        return parts

    def lookup(self, path: str) -> Union[dict, bytes]:
        """Найти узел VFS по пути или вызвать CommandError."""
        node = self.vfs
        for part in self.resolve(path):
            if not isinstance(node, dict) or part not in node:
                raise CommandError(f"{path}: {NOT_FOUND}")
            node = node[part]
        return node

    def read_file(self, path: str) -> bytes:
        """Вернуть содержимое файла или вызвать CommandError."""
        node = self.lookup(path)
        if isinstance(node, dict):
            raise CommandError(f"{path}: это каталог")
        return node

    def cmd_ls(self, args: List[str]) -> Result:
        """ls [ПУТЬ]: имена в каталоге (каталоги со «/») или имя файла."""
        if args[1:]:
            raise CommandError(TOO_MANY)
        path = args[0] if args else "."
        node = self.lookup(path)
        if not isinstance(node, dict):
            return Result(path)
        names = [
            name + "/" if isinstance(child, dict) else name
            for name, child in sorted(node.items())
        ]
        return Result("\n".join(names))

    def cmd_cd(self, args: List[str]) -> Result:
        """cd [ПУТЬ]: сменить каталог, без аргумента перейти в корень."""
        if args[1:]:
            raise CommandError(TOO_MANY)
        path = args[0] if args else ROOT
        if not isinstance(self.lookup(path), dict):
            raise CommandError(f"{path}: не каталог")
        self.cwd = ROOT + "/".join(self.resolve(path))
        return Result("")

    def cmd_echo(self, args: List[str]) -> Result:
        """echo [СЛОВО...]: вывести аргументы через пробел."""
        return Result(" ".join(args))

    def cmd_tac(self, args: List[str]) -> Result:
        """tac ФАЙЛ...: вывести строки каждого файла с конца."""
        if not args:
            raise CommandError("использование: tac ФАЙЛ...")
        contents = [self.read_file(path) for path in args]
        parts = [format_content(reverse_lines(data)) for data in contents]
        return Result("\n".join(part for part in parts if part))

    def cmd_exit(self, args: List[str]) -> Result:
        """exit: завершить работу эмулятора."""
        if args:
            raise CommandError(TOO_MANY)
        return Result("", should_exit=True)

    def run(self, line: str) -> Result:
        """Разобрать строку и выполнить команду."""
        try:
            words = shlex.split(line)
        except ValueError:
            return Result("синтаксическая ошибка: незакрытая кавычка", True)
        if not words:
            return Result("")
        handler = self.commands.get(words[0])
        if handler is None:
            return Result(f"{words[0]}: команда не найдена", True)
        try:
            return handler(words[1:])
        except CommandError as error:
            return Result(f"{words[0]}: {error}", True)


def read_script(path: str) -> List[str]:
    """Прочитать стартовый скрипт (UTF-8) и вернуть его строки."""
    try:
        with open(path, encoding="utf-8-sig") as script_file:
            return script_file.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ScriptError(f"не удалось прочитать скрипт '{path}': {error}")


def script_commands(lines: Iterable[str]) -> List[str]:
    """Оставить в скрипте команды: без пустых строк и комментариев."""
    texts = [line.strip() for line in lines]
    return [text for text in texts if text and not text.startswith(COMMENT)]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Разобрать параметры командной строки: --vfs и --script."""
    parser = argparse.ArgumentParser(
        prog="emulator",
        description="Эмулятор командной строки UNIX-подобной ОС (GUI).",
        allow_abbrev=False,
    )
    parser.add_argument("--vfs", metavar="PATH", help="путь к ZIP-архиву VFS")
    parser.add_argument(
        "--script", metavar="PATH", help="путь к стартовому скрипту"
    )
    return parser.parse_args(argv)


def format_debug(args: argparse.Namespace) -> str:
    """Отладочный вывод всех параметров запуска."""
    vfs = NOT_SET if args.vfs is None else args.vfs
    script = NOT_SET if args.script is None else args.script
    return (
        "[debug] Параметры запуска:\n"
        f"[debug]   --vfs    = {vfs}\n"
        f"[debug]   --script = {script}"
    )


def get_user_host() -> Tuple[str, str]:
    """Имя пользователя и имя компьютера из реальной ОС."""
    try:
        user = getpass.getuser()
    except (KeyError, OSError):
        user = UNKNOWN
    return user, socket.gethostname() or UNKNOWN


def format_title(user: str, host: str) -> str:
    """Заголовок окна: Эмулятор - [user@host]."""
    return f"Эмулятор - [{user}@{host}]"


def format_prompt(user: str, host: str, cwd: str) -> str:
    """Приглашение: user@host:/текущий/каталог$."""
    return f"{user}@{host}:{cwd}$"


class App:
    """Окно эмулятора: область вывода, приглашение и строка ввода."""

    def __init__(self, root: tk.Tk, args: argparse.Namespace) -> None:
        """Создать окно, показать параметры, загрузить VFS и скрипт."""
        self.root = root
        self.args = args
        self.user, self.host = get_user_host()
        self.shell = Shell({})
        self.steps = iter(())
        root.title(format_title(self.user, self.host))
        root.geometry(WINDOW_SIZE)
        self.build_widgets()
        self.print(WELCOME_TEXT)
        self.print(format_debug(args) + "\n")
        self.load_vfs()
        if args.script is not None:
            root.after(STEP_DELAY_MS, self.start_script)

    def prompt(self) -> str:
        """Приглашение с текущим каталогом."""
        return format_prompt(self.user, self.host, self.shell.cwd)

    def build_widgets(self) -> None:
        """Создать область вывода, приглашение и поле ввода."""
        self.output = scrolledtext.ScrolledText(
            self.root, bg=BG_COLOR, fg=FG_COLOR, font=FONT,
            state=tk.DISABLED, wrap=tk.WORD,
        )
        self.output.tag_config(ERROR_TAG, foreground=ERROR_COLOR)
        self.output.pack(fill=tk.BOTH, expand=True)
        bottom = tk.Frame(self.root, bg=BG_COLOR)
        bottom.pack(fill=tk.X)
        self.label = tk.Label(
            bottom, text=self.prompt(), bg=BG_COLOR, fg=FG_COLOR, font=FONT
        )
        self.label.pack(side=tk.LEFT)
        self.entry = tk.Entry(
            bottom, bg=BG_COLOR, fg=FG_COLOR, font=FONT,
            insertbackground=FG_COLOR, relief=tk.FLAT,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()

    def print(self, text: str, is_error: bool = False) -> None:
        """Добавить текст в конец области вывода."""
        tags = (ERROR_TAG,) if is_error else ()
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text, tags)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def load_vfs(self) -> None:
        """Загрузить VFS из ZIP-архива в память, если задан --vfs."""
        if self.args.vfs is None:
            return
        try:
            self.shell.vfs = load_vfs(self.args.vfs)
        except VfsError as error:
            self.print(f"{error}\n", True)
            return
        self.print(f"VFS загружена в память: {self.args.vfs}\n")

    def run_line(self, line: str) -> bool:
        """Выполнить строку, показать ввод и вывод; True при exit."""
        prompt = self.prompt()
        result = self.shell.run(line)
        self.print(f"{prompt} {line}\n")
        if result.output:
            self.print(result.output + "\n", result.is_error)
        self.label.config(text=self.prompt())
        if result.should_exit:
            self.root.destroy()
        return result.should_exit

    def on_enter(self, _event: tk.Event) -> None:
        """Нажат Enter: выполнить введённую команду."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.run_line(line)

    def start_script(self) -> None:
        """Прочитать стартовый скрипт и начать его выполнение."""
        try:
            lines = read_script(self.args.script)
        except ScriptError as error:
            self.print(f"{error}\n", True)
            return
        self.print(f"Выполнение стартового скрипта: {self.args.script}\n")
        self.steps = iter(script_commands(lines))
        self.next_step()

    def next_step(self) -> None:
        """Выполнить очередную строку скрипта, запланировать следующую."""
        line = next(self.steps, None)
        if line is None:
            self.print("Стартовый скрипт выполнен.\n")
        elif not self.run_line(line):
            self.root.after(STEP_DELAY_MS, self.next_step)


def main(argv: Optional[List[str]] = None) -> None:
    """Разобрать параметры и запустить окно эмулятора."""
    args = parse_args(argv)
    root = tk.Tk()
    App(root, args)
    root.mainloop()


if __name__ == "__main__":
    main()
