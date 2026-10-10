"""Команды эмулятора и их выполнение."""

from typing import Callable, Dict, List, Optional

from emulator.errors import CommandError, reject_args
from emulator.fs_commands import cmd_cd, cmd_ls
from emulator.result import CommandResult
from emulator.session import Session
from emulator.shell_parser import ParseError, parse_line
from emulator.text_commands import cmd_echo, cmd_tac
from emulator.vfs_commands import (
    INFO_NAME,
    SHOW_NAME,
    TREE_NAME,
    cmd_vfs_info,
    cmd_vfs_show,
    cmd_vfs_tree,
)

EXIT_NAME = "exit"

Handler = Callable[[List[str], Session], CommandResult]


def cmd_exit(args: List[str], _session: Session) -> CommandResult:
    """Команда exit: завершает работу эмулятора.

    Если переданы аргументы, возвращает ошибку и не завершает работу.
    """
    reject_args(args)
    return CommandResult("", should_exit=True)


COMMANDS: Dict[str, Handler] = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "echo": cmd_echo,
    "tac": cmd_tac,
    EXIT_NAME: cmd_exit,
    INFO_NAME: cmd_vfs_info,
    TREE_NAME: cmd_vfs_tree,
    SHOW_NAME: cmd_vfs_show,
}


def _error(text: str) -> CommandResult:
    """Сформировать результат-ошибку с заданным текстом."""
    return CommandResult(text, is_error=True)


def execute(line: str, session: Optional[Session] = None) -> CommandResult:
    """Разобрать строку ввода и выполнить соответствующую команду.

    Args:
        line: строка, введённая пользователем.
        session: состояние сеанса (VFS и текущий каталог); если None,
            используется пустое состояние без VFS.

    Returns:
        CommandResult. Для пустой строки вывод пустой; для неизвестной
        команды и ошибок разбора возвращается сообщение об ошибке.
    """
    session = Session() if session is None else session
    try:
        parsed = parse_line(line)
    except ParseError as error:
        return _error(f"синтаксическая ошибка: {error}")
    if parsed is None:
        return CommandResult("")
    handler = COMMANDS.get(parsed.command)
    if handler is None:
        return _error(f"{parsed.command}: команда не найдена")
    try:
        return handler(parsed.args, session)
    except CommandError as error:
        return _error(f"{parsed.command}: {error}")
