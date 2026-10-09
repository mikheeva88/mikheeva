"""Параметры командной строки эмулятора и их отладочный вывод."""

import argparse
from dataclasses import dataclass
from typing import Optional, Sequence

PROGRAM_NAME = "emulator"
NOT_SET_TEXT = "(не задан)"
DEBUG_PREFIX = "[debug]"


@dataclass(frozen=True)
class Config:
    """Параметры запуска эмулятора.

    Attributes:
        vfs_path: путь к физическому расположению VFS или None.
        script_path: путь к стартовому скрипту или None.
    """

    vfs_path: Optional[str] = None
    script_path: Optional[str] = None


def build_arg_parser() -> argparse.ArgumentParser:
    """Создать разборщик параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Эмулятор командной строки UNIX-подобной ОС (GUI).",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--vfs", metavar="PATH",
        help="путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--script", metavar="PATH",
        help="путь к стартовому скрипту с командами эмулятора",
    )
    return parser


def parse_args(argv: Optional[Sequence[str]] = None) -> Config:
    """Разобрать параметры командной строки.

    При неизвестном параметре или параметре без значения argparse
    выводит сообщение об ошибке и завершает программу (SystemExit).

    Args:
        argv: список аргументов; если None, берётся sys.argv[1:].

    Returns:
        Config с заданными значениями (None для не заданных).
    """
    namespace = build_arg_parser().parse_args(argv)
    return Config(vfs_path=namespace.vfs, script_path=namespace.script)


def _show_value(value: Optional[str]) -> str:
    """Вернуть значение параметра или текст «не задан»."""
    return NOT_SET_TEXT if value is None else value


def format_debug(config: Config) -> str:
    """Сформировать отладочный вывод всех параметров запуска.

    Args:
        config: параметры запуска эмулятора.

    Returns:
        Многострочный текст, по строке на каждый параметр.
    """
    lines = [
        f"{DEBUG_PREFIX} Параметры запуска:",
        f"{DEBUG_PREFIX}   --vfs    = {_show_value(config.vfs_path)}",
        f"{DEBUG_PREFIX}   --script = {_show_value(config.script_path)}",
    ]
    return "\n".join(lines)
