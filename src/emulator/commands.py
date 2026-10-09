"""Команды эмулятора: заглушки ls и cd, а также команда exit."""

from typing import Callable, Dict, List, NamedTuple

from emulator.shell_parser import parse_line

NO_ARGS_TEXT = "(нет)"
EXIT_NAME = "exit"


class CommandResult(NamedTuple):
    """Результат выполнения команды.

    Attributes:
        output: текст, который нужно показать пользователю.
        is_error: True, если текст является сообщением об ошибке.
        should_exit: True, если эмулятор нужно завершить.
    """

    output: str
    is_error: bool = False
    should_exit: bool = False


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


def cmd_ls(args: List[str]) -> CommandResult:
    """Заглушка команды ls: выводит своё имя и аргументы."""
    return CommandResult(format_stub("ls", args))


def cmd_cd(args: List[str]) -> CommandResult:
    """Заглушка команды cd: выводит своё имя и аргументы."""
    return CommandResult(format_stub("cd", args))


def cmd_exit(args: List[str]) -> CommandResult:
    """Команда exit: завершает работу эмулятора.

    Если переданы аргументы, возвращает ошибку и не завершает работу.
    """
    if args:
        message = f"{EXIT_NAME}: слишком много аргументов"
        return CommandResult(message, is_error=True)
    return CommandResult("", should_exit=True)


COMMANDS: Dict[str, Callable[[List[str]], CommandResult]] = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    EXIT_NAME: cmd_exit,
}


def execute(line: str) -> CommandResult:
    """Разобрать строку ввода и выполнить соответствующую команду.

    Args:
        line: строка, введённая пользователем.

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
    return handler(parsed.args)
