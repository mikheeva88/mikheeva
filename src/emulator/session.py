"""Состояние сеанса эмулятора: загруженная VFS и текущий каталог."""

from dataclasses import dataclass
from typing import Optional

from emulator.errors import CommandError
from emulator.paths import ROOT_PATH, normalize
from emulator.vfs import Vfs, VfsNode

NO_VFS_TEXT = "VFS не загружена (задайте параметр --vfs)"
NOT_FOUND_TEXT = "нет такого файла или каталога"


@dataclass
class Session:
    """Состояние эмулятора, общее для всех команд.

    Attributes:
        vfs: загруженная VFS или None, если она не задана.
        cwd: текущий каталог (абсолютный путь).
        prev_cwd: предыдущий каталог (для команды «cd -»).
    """

    vfs: Optional[Vfs] = None
    cwd: str = ROOT_PATH
    prev_cwd: str = ROOT_PATH

    def require_vfs(self) -> Vfs:
        """Вернуть VFS или вызвать CommandError, если она не загружена."""
        if self.vfs is None:
            raise CommandError(NO_VFS_TEXT)
        return self.vfs

    def resolve(self, path: str) -> str:
        """Превратить путь пользователя в абсолютный нормальный путь."""
        return normalize(self.cwd, path)

    def lookup(self, path: str) -> VfsNode:
        """Найти узел VFS по пути относительно текущего каталога.

        Args:
            path: абсолютный или относительный путь.

        Returns:
            Найденный узел.

        Raises:
            CommandError: VFS не загружена или путь не найден.
        """
        node = self.require_vfs().find(self.resolve(path))
        if node is None:
            raise CommandError(f"{path}: {NOT_FOUND_TEXT}")
        return node
