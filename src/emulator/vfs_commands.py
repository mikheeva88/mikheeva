"""Служебные команды для работы с VFS: vfs-info, vfs-tree, vfs-show."""

from typing import List

from emulator.content import format_content
from emulator.errors import CommandError, reject_args
from emulator.result import CommandResult
from emulator.session import Session
from emulator.vfs import VfsNode

INFO_NAME = "vfs-info"
TREE_NAME = "vfs-tree"
SHOW_NAME = "vfs-show"
SHOW_ARG_COUNT = 1
BRANCH = "|-- "
LAST_BRANCH = "`-- "
PIPE_PAD = "|   "
LAST_PAD = "    "


def cmd_vfs_info(args: List[str], session: Session) -> CommandResult:
    """Команда vfs-info: источник и статистика загруженной VFS."""
    vfs = session.require_vfs()
    reject_args(args)
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


def cmd_vfs_tree(args: List[str], session: Session) -> CommandResult:
    """Команда vfs-tree: дерево всех каталогов и файлов VFS."""
    vfs = session.require_vfs()
    reject_args(args)
    return CommandResult("\n".join(["/"] + tree_lines(vfs.root)))


def cmd_vfs_show(args: List[str], session: Session) -> CommandResult:
    """Команда vfs-show ПУТЬ: вывести содержимое файла VFS."""
    session.require_vfs()
    if len(args) != SHOW_ARG_COUNT:
        raise CommandError("использование: vfs-show ПУТЬ")
    node = session.lookup(args[0])
    if node.is_dir:
        raise CommandError(f"{args[0]}: это каталог")
    return CommandResult(format_content(node.data))
