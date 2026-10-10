"""Ошибки выполнения команд эмулятора."""

from typing import List

TOO_MANY_TEXT = "слишком много аргументов"


class CommandError(Exception):
    """Ошибка команды: текст показывается пользователю.

    Имя команды к тексту добавляется при выполнении (см. execute).
    """


def reject_args(args: List[str]) -> None:
    """Вызвать CommandError, если переданы аргументы.

    Args:
        args: аргументы команды.

    Raises:
        CommandError: если список аргументов не пуст.
    """
    if args:
        raise CommandError(TOO_MANY_TEXT)
