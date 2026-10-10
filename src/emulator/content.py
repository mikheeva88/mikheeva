"""Представление содержимого файлов для вывода на экран."""

import base64

EMPTY_FILE_TEXT = "(файл пуст)"
BINARY_TEXT = "(двоичный файл, base64)"
NUL_BYTE = b"\x00"


def is_text(data: bytes) -> bool:
    """Проверить, что данные являются текстом UTF-8 без нулевых байтов."""
    if NUL_BYTE in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def format_content(data: bytes) -> str:
    """Представить содержимое файла для вывода на экран.

    Текст выводится как есть, двоичные данные кодируются в base64.

    Args:
        data: содержимое файла.

    Returns:
        Строка для вывода.
    """
    if not data:
        return EMPTY_FILE_TEXT
    if is_text(data):
        return data.decode("utf-8").replace("\r\n", "\n").rstrip("\n")
    encoded = base64.encodebytes(data).decode("ascii").rstrip("\n")
    return f"{BINARY_TEXT}\n{encoded}"
