"""Виртуальная файловая система (VFS) в памяти, загружаемая из ZIP.

Архив только читается: файлы не распаковываются на диск, а
содержимое хранится в оперативной памяти в виде дерева узлов.
"""

import zipfile
import zlib
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional

MAX_DEPTH = 100
LOAD_ERRORS = (
    OSError,
    zipfile.BadZipFile,
    RuntimeError,
    NotImplementedError,
    EOFError,
    zlib.error,
)


class VfsError(Exception):
    """Ошибка загрузки или разбора VFS."""


@dataclass
class VfsNode:
    """Узел VFS: каталог или файл.

    Attributes:
        name: имя узла (пустое для корня).
        is_dir: True для каталога.
        data: содержимое файла в байтах (для каталога пусто).
        children: вложенные узлы каталога по именам.
    """

    name: str
    is_dir: bool
    data: bytes = b""
    children: Dict[str, "VfsNode"] = field(default_factory=dict)


@dataclass(frozen=True)
class VfsStats:
    """Статистика VFS: число каталогов (без корня), файлов, размер."""

    dirs: int
    files: int
    size: int


def split_path(path: str) -> List[str]:
    """Разбить путь по «/» на части, отбросив пустые и «.»."""
    return [part for part in path.split("/") if part and part != "."]


class Vfs:
    """Виртуальная файловая система, целиком лежащая в памяти."""

    def __init__(self, root: VfsNode, source: str) -> None:
        """Создать VFS.

        Args:
            root: корневой каталог.
            source: путь к ZIP-архиву, из которого загружена VFS.
        """
        self.root = root
        self.source = source

    def find(self, path: str) -> Optional[VfsNode]:
        """Найти узел по пути от корня VFS.

        Args:
            path: путь вида «/a/b» или «a/b».

        Returns:
            Узел или None, если такого пути нет.
        """
        node = self.root
        for part in split_path(path):
            child = node.children.get(part) if node.is_dir else None
            if child is None:
                return None
            node = child
        return node

    def iter_nodes(self) -> Iterator[VfsNode]:
        """Обойти все узлы VFS, кроме корня."""
        stack = list(self.root.children.values())
        while stack:
            node = stack.pop()
            yield node
            stack.extend(node.children.values())

    def stats(self) -> VfsStats:
        """Посчитать каталоги, файлы и общий размер данных."""
        dirs = 0
        files = 0
        size = 0
        for node in self.iter_nodes():
            if node.is_dir:
                dirs += 1
            else:
                files += 1
                size += len(node.data)
        return VfsStats(dirs=dirs, files=files, size=size)


def _get_or_make_dir(parent: VfsNode, name: str, entry: str) -> VfsNode:
    """Вернуть вложенный каталог, создав его при необходимости."""
    node = parent.children.get(name)
    if node is None:
        node = VfsNode(name=name, is_dir=True)
        parent.children[name] = node
    elif not node.is_dir:
        raise VfsError(f"конфликт файла и каталога в записи '{entry}'")
    return node


def _add_entry(root: VfsNode, entry: str, data: bytes, is_dir: bool) -> None:
    """Добавить запись архива в дерево VFS.

    Args:
        root: корневой каталог.
        entry: имя записи в архиве.
        data: содержимое (для каталога пусто).
        is_dir: True, если запись является каталогом.

    Raises:
        VfsError: путь выходит за корень, слишком глубокий, повторяется
            или конфликтует с другой записью.
    """
    parts = split_path(entry)
    if ".." in parts:
        raise VfsError(f"недопустимый путь в архиве: '{entry}'")
    if len(parts) > MAX_DEPTH:
        raise VfsError(f"слишком глубокая вложенность: '{entry}'")
    if not parts:
        return
    node = root
    for part in parts[:-1]:
        node = _get_or_make_dir(node, part, entry)
    if is_dir:
        _get_or_make_dir(node, parts[-1], entry)
    elif parts[-1] in node.children:
        raise VfsError(f"повторяющаяся запись '{entry}'")
    else:
        node.children[parts[-1]] = VfsNode(parts[-1], False, data)


def _build_tree(archive: zipfile.ZipFile) -> VfsNode:
    """Прочитать все записи архива в память и построить дерево."""
    root = VfsNode(name="", is_dir=True)
    for info in archive.infolist():
        data = b"" if info.is_dir() else archive.read(info)
        _add_entry(root, info.filename, data, info.is_dir())
    return root


def load_vfs(path: str) -> Vfs:
    """Загрузить VFS из ZIP-архива в память.

    Архив только читается, на диск ничего не распаковывается.

    Args:
        path: путь к ZIP-архиву.

    Returns:
        Загруженная VFS.

    Raises:
        VfsError: архив не найден, повреждён или содержит
            недопустимые записи.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            root = _build_tree(archive)
    except LOAD_ERRORS as error:
        message = f"не удалось загрузить VFS '{path}': {error}"
        raise VfsError(message) from error
    return Vfs(root=root, source=path)
