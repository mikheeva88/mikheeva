import argparse
import base64
import collections
import getpass
import shlex
import socket
import tkinter as tk
import zipfile
from tkinter import scrolledtext

ROOT = "/"
DEFAULT_OWNER = ("root", "root")
TOO_MANY = "слишком много аргументов"
NOT_FOUND = "нет такого файла или каталога"
NOT_SET = "(не задан)"
STEP_DELAY_MS = 300
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
ERROR_COLOR = "#f48771"
FONT = ("Courier New", 12)
WELCOME_TEXT = (
    "Эмулятор командной строки.\n"
    "Команды: ls, cd, echo, tac, rmdir, chown, exit.\n"
)
Result = collections.namedtuple(
    "Result", "output is_error should_exit", defaults=(False, False)
)


class VfsError(Exception):
    pass


class CommandError(Exception):
    pass


def split_path(path):
    return [part for part in path.split("/") if part and part != "."]


def add_entry(root, name, data, is_dir):
    parts = split_path(name)
    if ".." in parts:
        raise VfsError(f"недопустимый путь в архиве: '{name}'")
    folder = root
    for part in parts if is_dir else parts[:-1]:
        folder = folder.setdefault(part, {})
        if not isinstance(folder, dict):
            raise VfsError(f"конфликт имён в записи '{name}'")
    if parts and not is_dir:
        if parts[-1] in folder:
            raise VfsError(f"повторяющаяся запись '{name}'")
        folder[parts[-1]] = data


def load_vfs(path):
    root = {}
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                data = b"" if info.is_dir() else archive.read(info)
                add_entry(root, info.filename, data, info.is_dir())
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        message = f"не удалось загрузить VFS '{path}': {error}"
        raise VfsError(message) from error
    return root


def reverse_lines(data):
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    lines.reverse()
    return b"\n".join(lines)


def format_content(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = "\x00"
    if "\x00" in text:
        encoded = base64.encodebytes(data).decode("ascii").rstrip("\n")
        return f"(двоичный файл, base64)\n{encoded}"
    return text.replace("\r\n", "\n").rstrip("\n")


class Shell:
    def __init__(self, vfs):
        self.vfs = vfs
        self.cwd = ROOT
        self.owners = {}
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "echo": self.cmd_echo,
            "tac": self.cmd_tac,
            "rmdir": self.cmd_rmdir,
            "chown": self.cmd_chown,
            "exit": self.cmd_exit,
        }

    def resolve(self, path):
        parts = [] if path.startswith(ROOT) else split_path(self.cwd)
        for part in split_path(path):
            if part != "..":
                parts.append(part)
            elif parts:
                parts.pop()
        return parts

    def full_path(self, parts):
        return ROOT + "/".join(parts)

    def lookup(self, path):
        node = self.vfs
        for part in self.resolve(path):
            if not isinstance(node, dict) or part not in node:
                raise CommandError(f"{path}: {NOT_FOUND}")
            node = node[part]
        return node

    def read_file(self, path):
        node = self.lookup(path)
        if isinstance(node, dict):
            raise CommandError(f"{path}: это каталог")
        return node

    def ls_line(self, label, parts, node, long_format):
        if not long_format:
            return label
        owner, group = self.owners.get(self.full_path(parts), DEFAULT_OWNER)
        kind, size = ("d", 0) if isinstance(node, dict) else ("-", len(node))
        return f"{kind} {owner} {group} {size:>6} {label}"

    def cmd_ls(self, args):
        debug_info = f"[debug] ls: {args}"
        long_format = False
        paths = []
        for arg in args:
            if arg == "-l":
                long_format = True
            elif arg.startswith("-"):
                raise CommandError(f"неверный ключ: {arg}")
            else:
                paths.append(arg)
        if paths[1:]:
            raise CommandError(TOO_MANY)
        path = paths[0] if paths else "."
        node = self.lookup(path)
        parts = self.resolve(path)
        if not isinstance(node, dict):
            return Result(f"{debug_info}\n{self.ls_line(path, parts, node, long_format)}")
        lines = [debug_info]
        for name, child in sorted(node.items()):
            label = name + "/" if isinstance(child, dict) else name
            line = self.ls_line(label, parts + [name], child, long_format)
            lines.append(line)
        return Result("\n".join(lines))

    def cmd_cd(self, args):
        debug_info = f"[debug] cd: {args}"
        if args[1:]:
            raise CommandError(TOO_MANY)
        path = args[0] if args else ROOT
        if not isinstance(self.lookup(path), dict):
            raise CommandError(f"{path}: не каталог")
        self.cwd = self.full_path(self.resolve(path))
        return Result(debug_info)

    def cmd_echo(self, args):
        return Result(" ".join(args))

    def cmd_tac(self, args):
        if not args:
            raise CommandError("использование: tac ФАЙЛ...")
        contents = [self.read_file(path) for path in args]
        parts = [format_content(reverse_lines(data)) for data in contents]
        return Result("\n".join(part for part in parts if part))

    def remove_dir(self, path):
        node = self.lookup(path)
        parts = self.resolve(path)
        if not parts:
            raise CommandError(f"{path}: нельзя удалить корень")
        if not isinstance(node, dict):
            raise CommandError(f"{path}: не каталог")
        if node:
            raise CommandError(f"{path}: каталог не пуст")
        if self.full_path(parts) == self.cwd:
            raise CommandError(f"{path}: нельзя удалить текущий каталог")
        parent = self.lookup(self.full_path(parts[:-1]))
        del parent[parts[-1]]
        self.owners.pop(self.full_path(parts), None)

    def cmd_rmdir(self, args):
        if not args:
            raise CommandError("использование: rmdir КАТАЛОГ...")
        for path in args:
            self.remove_dir(path)
        return Result("")

    def cmd_chown(self, args):
        if not args[1:]:
            message = "использование: chown ВЛАДЕЛЕЦ[:ГРУППА] ПУТЬ..."
            raise CommandError(message)
        owner, _, group = args[0].partition(":")
        if not owner:
            raise CommandError(f"неверный владелец: '{args[0]}'")
        for path in args[1:]:
            self.lookup(path)
        for path in args[1:]:
            key = self.full_path(self.resolve(path))
            old_group = self.owners.get(key, DEFAULT_OWNER)[1]
            self.owners[key] = (owner, group or old_group)
        return Result("")

    def cmd_exit(self, args):
        if args:
            raise CommandError(TOO_MANY)
        return Result("", should_exit=True)

    def run(self, line):
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


def read_script(path):
    with open(path, encoding="utf-8-sig") as script_file:
        lines = [line.strip() for line in script_file]
    return [line for line in lines if line and not line.startswith("#")]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="emulator", allow_abbrev=False)
    parser.add_argument("--vfs", metavar="PATH", help="путь к ZIP-архиву VFS")
    parser.add_argument(
        "--script", metavar="PATH", help="путь к стартовому скрипту"
    )
    return parser.parse_args(argv)


def format_debug(args):
    vfs = NOT_SET if args.vfs is None else args.vfs
    script = NOT_SET if args.script is None else args.script
    return (
        "[debug] Параметры запуска:\n"
        f"[debug]   --vfs    = {vfs}\n"
        f"[debug]   --script = {script}"
    )


class App:
    def __init__(self, root, args):
        self.root = root
        self.args = args
        self.shell = Shell({})
        self.steps = iter(())
        try:
            self.user = getpass.getuser()
        except (KeyError, OSError):
            self.user = "unknown"
        self.host = socket.gethostname()
        root.title(f"Эмулятор - [{self.user}@{self.host}]")
        root.geometry("800x500")
        self.build_widgets()
        self.show(WELCOME_TEXT + format_debug(args) + "\n")
        self.load_vfs()
        if args.script is not None:
            root.after(STEP_DELAY_MS, self.start_script)

    def prompt(self):
        return f"{self.user}@{self.host}:{self.shell.cwd}$"

    def build_widgets(self):
        self.output = scrolledtext.ScrolledText(
            self.root, bg=BG_COLOR, fg=FG_COLOR, font=FONT,
            state=tk.DISABLED, wrap=tk.WORD,
        )
        self.output.tag_config("error", foreground=ERROR_COLOR)
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

    def show(self, text, is_error=False):
        tags = ("error",) if is_error else ()
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text, tags)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def load_vfs(self):
        if self.args.vfs is None:
            return
        try:
            self.shell.vfs = load_vfs(self.args.vfs)
        except VfsError as error:
            self.show(f"{error}\n", True)
            return
        self.show(f"VFS загружена в память: {self.args.vfs}\n")

    def run_line(self, line):
        prompt = self.prompt()
        result = self.shell.run(line)
        self.show(f"{prompt} {line}\n")
        if result.output:
            self.show(result.output + "\n", result.is_error)
        self.label.config(text=self.prompt())
        if result.should_exit:
            self.root.destroy()
        return result.should_exit

    def on_enter(self, _event):
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.run_line(line)

    def start_script(self):
        try:
            self.steps = iter(read_script(self.args.script))
        except (OSError, UnicodeDecodeError) as error:
            message = f"не удалось прочитать скрипт '{self.args.script}'"
            self.show(f"{message}: {error}\n", True)
            return
        self.show(f"Выполнение стартового скрипта: {self.args.script}\n")
        self.next_step()

    def next_step(self):
        line = next(self.steps, None)
        if line is None:
            self.show("Стартовый скрипт выполнен.\n")
        elif not self.run_line(line):
            self.root.after(STEP_DELAY_MS, self.next_step)


def main(argv=None):
    args = parse_args(argv)
    root = tk.Tk()
    App(root, args)
    root.mainloop()


if __name__ == "__main__":
    main()
