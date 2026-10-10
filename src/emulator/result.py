"""Результат выполнения команды эмулятора."""

from typing import NamedTuple


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
