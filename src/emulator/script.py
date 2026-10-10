"""Загрузка и выполнение стартового скрипта эмулятора."""

from typing import Iterable, Iterator, List, Optional, Tuple

from emulator.commands import execute
from emulator.result import CommandResult
from emulator.session import Session

COMMENT_PREFIX = "#"
SCRIPT_ENCODING = "utf-8-sig"


class ScriptError(Exception):
    """Ошибка чтения стартового скрипта."""


def load_script(path: str) -> List[str]:
    """Прочитать стартовый скрипт и вернуть его строки.

    Args:
        path: путь к текстовому файлу в кодировке UTF-8.

    Returns:
        Список строк файла без символов перевода строки.

    Raises:
        ScriptError: если файл не найден или не читается.
    """
    try:
        with open(path, encoding=SCRIPT_ENCODING) as script_file:
            return script_file.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        message = f"не удалось прочитать скрипт '{path}': {error}"
        raise ScriptError(message) from error


def is_skipped(line: str) -> bool:
    """Проверить, что строку не нужно выполнять.

    Пропускаются пустые строки и комментарии (начинаются с «#»).
    """
    stripped = line.strip()
    return not stripped or stripped.startswith(COMMENT_PREFIX)


def iter_commands(lines: Iterable[str]) -> Iterator[str]:
    """Выбрать из строк скрипта команды для выполнения.

    Args:
        lines: строки скрипта.

    Yields:
        Строки без лишних пробелов; пустые и комментарии пропущены.
    """
    for line in lines:
        if not is_skipped(line):
            yield line.strip()


def run_script(
    lines: Iterable[str],
    session: Optional[Session] = None,
) -> Iterator[Tuple[str, CommandResult]]:
    """Последовательно выполнять строки скрипта.

    Строки с ошибками не прерывают выполнение: их результат
    (с флагом is_error) возвращается, и работа идёт дальше.
    После команды exit выполнение останавливается.

    Args:
        lines: строки скрипта.
        session: состояние сеанса; если None, создаётся пустое.

    Yields:
        Пары (строка без лишних пробелов, результат команды).
    """
    session = Session() if session is None else session
    for text in iter_commands(lines):
        result = execute(text, session)
        yield text, result
        if result.should_exit:
            return
