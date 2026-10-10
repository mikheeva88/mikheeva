"""Команды эмулятора: ls, cd (заглушки), exit и служебные команды VFS."""

from typing import Callable, Dict, List, Optional

from emulator.result import CommandResult
from emulator.shell_parser import parse_line
from emulator.vfs import Vfs
from emulator.vfs_commands import (
    INFO_NAME,
    SHOW_NAME,
    TREE_NAME,
    cmd_vfs_info,
    cmd_vfs_show,
    cmd_vfs_tree,
)

NO_ARGS_TEXT = "(нет)"
EXIT_NAME = "exit"

Handler = Callable[[List[str], Optional[Vfs]], CommandResult]


def format_stub(name: str, args: List[str]) -> str:
    """Сформировать вывод команды-заглушки: имя и аргументы.

    Args:
        name: имя команды.
        args: список аргументов команды.

    Returns:
        Многострочный текст с именем команды и её аргументами.
    """
    args_text = " ".join(args) if args else NO_ARGS_TEXT
    return f"Команда: {name}\nАргументы ({len(args)}): {args_text}"


def cmd_ls(args: List[str], _vfs: Optional[Vfs]) -> CommandResult:
    """Заглушка команды ls: выводит своё имя и аргументы."""
    return CommandResult(format_stub("ls", args))


def cmd_cd(args: List[str], _vfs: Optional[Vfs]) -> CommandResult:
    """Заглушка команды cd: выводит своё имя и аргументы."""
    return CommandResult(format_stub("cd", args))


def cmd_exit(args: List[str], _vfs: Optional[Vfs]) -> CommandResult:
    """Команда exit: завершает работу эмулятора.

    Если переданы аргументы, возвращает ошибку и не завершает работу.
    """
    if args:
        message = f"{EXIT_NAME}: слишком много аргументов"
        return CommandResult(message, is_error=True)
    return CommandResult("", should_exit=True)


COMMANDS: Dict[str, Handler] = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    EXIT_NAME: cmd_exit,
    INFO_NAME: cmd_vfs_info,
    TREE_NAME: cmd_vfs_tree,
    SHOW_NAME: cmd_vfs_show,
}


def execute(line: str, vfs: Optional[Vfs] = None) -> CommandResult:
    """Разобрать строку ввода и выполнить соответствующую команду.

    Args:
        line: строка, введённая пользователем.
        vfs: загруженная VFS или None, если она не задана.

    Returns:
        CommandResult. Для пустой строки вывод пустой; для неизвестной
        команды возвращается сообщение об ошибке.
    """
    parsed = parse_line(line)
    if parsed is None:
        return CommandResult("")
    handler = COMMANDS.get(parsed.command)
    if handler is None:
        message = f"{parsed.command}: команда не найдена"
        return CommandResult(message, is_error=True)
    return handler(parsed.args, vfs)
