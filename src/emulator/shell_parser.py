"""Простой парсер строки, введённой пользователем в эмуляторе."""

from typing import List, NamedTuple, Optional


class ParsedLine(NamedTuple):
    """Разобранная строка ввода.

    Attributes:
        command: имя команды (первое слово строки).
        args: список аргументов (все остальные слова).
    """

    command: str
    args: List[str]


def parse_line(line: str) -> Optional[ParsedLine]:
    """Разделить строку на команду и аргументы по пробельным символам.

    Несколько пробелов подряд считаются одним разделителем. Кавычки
    и экранирование на этом этапе не поддерживаются.

    Args:
        line: строка, введённая пользователем.

    Returns:
        ParsedLine или None, если строка пустая (нет ни одного слова).
    """
    words = line.split()
    if not words:
        return None
    return ParsedLine(command=words[0], args=words[1:])
