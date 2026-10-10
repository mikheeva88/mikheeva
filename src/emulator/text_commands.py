"""Текстовые команды: echo и tac."""

import re
from typing import List

from emulator.content import format_content
from emulator.errors import CommandError
from emulator.result import CommandResult
from emulator.session import Session

ESCAPE_OPTION = "-e"
ESCAPE_PATTERN = re.compile(r"\\(.)")
ESCAPES = {"n": "\n", "t": "\t", "\\": "\\"}
NEWLINE = b"\n"


def _replace_escape(match: "re.Match") -> str:
    """Заменить последовательность «\\x» на символ, если она известна."""
    return ESCAPES.get(match.group(1), match.group(0))


def cmd_echo(args: List[str], _session: Session) -> CommandResult:
    """Команда echo [-e] [СЛОВО...]: вывести аргументы через пробел.

    Ключ -e включает обработку последовательностей \\n, \\t и \\\\.
    """
    use_escapes = args[:1] == [ESCAPE_OPTION]
    words = args[1:] if use_escapes else args
    text = " ".join(words)
    if use_escapes:
        text = ESCAPE_PATTERN.sub(_replace_escape, text)
    return CommandResult(text)


def reverse_lines(data: bytes) -> bytes:
    """Записать строки данных в обратном порядке.

    Если у данных нет завершающего перевода строки, он добавляется
    к последней строке до переворота.

    Args:
        data: содержимое файла.

    Returns:
        Данные с обратным порядком строк (без завершающего перевода).
    """
    lines = data.split(NEWLINE)
    if lines[-1] == b"":
        lines.pop()
    lines.reverse()
    return NEWLINE.join(lines)


def _file_data(session: Session, path: str) -> bytes:
    """Вернуть содержимое файла по пути или вызвать CommandError."""
    node = session.lookup(path)
    if node.is_dir:
        raise CommandError(f"{path}: это каталог")
    return node.data


def cmd_tac(args: List[str], session: Session) -> CommandResult:
    """Команда tac ФАЙЛ...: вывести строки файлов в обратном порядке.

    Каждый файл переворачивается отдельно. Двоичные данные
    выводятся в base64. Если какой-либо файл недоступен, выводится
    только ошибка.
    """
    if not args:
        raise CommandError("использование: tac ФАЙЛ...")
    contents = [_file_data(session, path) for path in args]
    parts = [format_content(reverse_lines(data)) if data else ""
             for data in contents]
    return CommandResult("\n".join(part for part in parts if part))
