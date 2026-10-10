"""Получение данных реальной ОС: имя пользователя и имя компьютера."""

import getpass
import socket
from typing import Optional

UNKNOWN_NAME = "unknown"


def get_username() -> str:
    """Вернуть имя текущего пользователя ОС или "unknown"."""
    try:
        return getpass.getuser() or UNKNOWN_NAME
    except (KeyError, OSError):
        return UNKNOWN_NAME


def get_hostname() -> str:
    """Вернуть имя компьютера (hostname) или "unknown"."""
    try:
        return socket.gethostname() or UNKNOWN_NAME
    except OSError:
        return UNKNOWN_NAME


def format_title(username: Optional[str], hostname: Optional[str]) -> str:
    """Сформировать заголовок окна вида «Эмулятор - [user@host]»."""
    return f"Эмулятор - [{username}@{hostname}]"


def format_prompt(
    username: Optional[str],
    hostname: Optional[str],
    cwd: str = "/",
) -> str:
    """Сформировать приглашение вида «user@host:/текущий/каталог$»."""
    return f"{username}@{hostname}:{cwd}$"
