"""Служебные команды для работы с VFS: vfs-info, vfs-tree, vfs-show."""

import base64
from typing import List, Optional

from emulator.result import CommandResult
from emulator.vfs import Vfs, VfsNode

INFO_NAME = "vfs-info"
TREE_NAME = "vfs-tree"
SHOW_NAME = "vfs-show"
SHOW_ARG_COUNT = 1
NO_VFS_TEXT = "VFS не загружена (задайте параметр --vfs)"
TOO_MANY_TEXT = "слишком много аргументов"
EMPTY_FILE_TEXT = "(файл пуст)"
BINARY_TEXT = "(двоичный файл, base64)"
NUL_BYTE = b"\x00"
BRANCH = "|-- "
LAST_BRANCH = "`-- "
PIPE_PAD = "|   "
LAST_PAD = "    "


def _error(name: str, text: str) -> CommandResult:
    """Сформировать результат-ошибку вида «имя: текст»."""
    return CommandResult(f"{name}: {text}", is_error=True)


def _check_no_args(
    name: str, args: List[str], vfs: Optional[Vfs],
) -> Optional[CommandResult]:
    """Проверить, что VFS загружена и аргументов нет.

    Returns:
        Результат-ошибку или None, если проверка пройдена.
    """
    if vfs is None:
        return _error(name, NO_VFS_TEXT)
    if args:
        return _error(name, TOO_MANY_TEXT)
    return None


def cmd_vfs_info(args: List[str], vfs: Optional[Vfs]) -> CommandResult:
    """Команда vfs-info: источник и статистика загруженной VFS."""
    error = _check_no_args(INFO_NAME, args, vfs)
    if error:
        return error
    stats = vfs.stats()
    lines = [
        f"VFS: {vfs.source}",
        f"Каталогов (без корня): {stats.dirs}",
        f"Файлов: {stats.files}",
        f"Общий размер: {stats.size} B",
    ]
    return CommandResult("\n".join(lines))


def _node_label(node: VfsNode) -> str:
    """Подпись узла в дереве: каталог со «/», файл с размером."""
    if node.is_dir:
        return f"{node.name}/"
    return f"{node.name} ({len(node.data)} B)"


def _sort_key(node: VfsNode) -> tuple:
    """Ключ сортировки: сначала каталоги, потом файлы, по имени."""
    return (not node.is_dir, node.name)


def tree_lines(node: VfsNode, prefix: str = "") -> List[str]:
    """Построить строки дерева для содержимого каталога.

    Args:
        node: каталог, содержимое которого выводится.
        prefix: отступ, накопленный для вложенных уровней.

    Returns:
        Список строк дерева.
    """
    lines = []
    children = sorted(node.children.values(), key=_sort_key)
    for child in children:
        is_last = child is children[-1]
        branch = LAST_BRANCH if is_last else BRANCH
        lines.append(prefix + branch + _node_label(child))
        if child.is_dir:
            pad = LAST_PAD if is_last else PIPE_PAD
            lines.extend(tree_lines(child, prefix + pad))
    return lines


def cmd_vfs_tree(args: List[str], vfs: Optional[Vfs]) -> CommandResult:
    """Команда vfs-tree: дерево всех каталогов и файлов VFS."""
    error = _check_no_args(TREE_NAME, args, vfs)
    if error:
        return error
    return CommandResult("\n".join(["/"] + tree_lines(vfs.root)))


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


def cmd_vfs_show(args: List[str], vfs: Optional[Vfs]) -> CommandResult:
    """Команда vfs-show ПУТЬ: вывести содержимое файла VFS."""
    if vfs is None:
        return _error(SHOW_NAME, NO_VFS_TEXT)
    if len(args) != SHOW_ARG_COUNT:
        return _error(SHOW_NAME, "использование: vfs-show ПУТЬ")
    node = vfs.find(args[0])
    if node is None:
        return _error(SHOW_NAME, f"{args[0]}: нет такого файла или каталога")
    if node.is_dir:
        return _error(SHOW_NAME, f"{args[0]}: это каталог")
    return CommandResult(format_content(node.data))
