"""Парсер строки, введённой пользователем в эмуляторе."""

import shlex
from typing import List, NamedTuple, Optional


class ParseError(Exception):
    """Ошибка разбора строки (например, незакрытая кавычка)."""


class ParsedLine(NamedTuple):
    """Разобранная строка ввода.

    Attributes:
        command: имя команды (первое слово строки).
        args: список аргументов (все остальные слова).
    """

    command: str
    args: List[str]


def parse_line(line: str) -> Optional[ParsedLine]:
    """Разделить строку на команду и аргументы.

    Слова разделяются пробельными символами, несколько пробелов подряд
    считаются одним разделителем. Кавычки (' и ") объединяют слова с
    пробелами в один аргумент, обратная косая черта экранирует символ.

    Args:
        line: строка, введённая пользователем.

    Returns:
        ParsedLine или None, если строка пустая (нет ни одного слова).

    Raises:
        ParseError: если кавычка не закрыта.
    """
    try:
        words = shlex.split(line)
    except ValueError as error:
        raise ParseError("незакрытая кавычка или экранирование") from error
    if not words:
        return None
    return ParsedLine(command=words[0], args=words[1:])
