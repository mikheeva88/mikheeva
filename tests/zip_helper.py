"""Вспомогательные классы и функции для тестов с VFS."""

import os
import tempfile
import unittest
import zipfile

from emulator.commands import execute
from emulator.session import Session
from emulator.vfs import load_vfs


def make_zip(path, entries):
    """Создать ZIP-архив по списку пар (имя записи, содержимое)."""
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries:
            archive.writestr(name, data)


class TempDirTestCase(unittest.TestCase):
    """Базовый класс тестов с временной папкой."""

    def setUp(self):
        """Создать временную папку, удаляемую после теста."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name

    def archive(self, entries, name="test.zip"):
        """Создать архив во временной папке и вернуть путь к нему."""
        path = os.path.join(self.folder, name)
        make_zip(path, entries)
        return path


class SessionTestCase(TempDirTestCase):
    """Базовый класс: сеанс с VFS из списка ENTRIES и вызов команд."""

    ENTRIES = []

    def setUp(self):
        """Загрузить VFS из ENTRIES и создать сеанс."""
        super().setUp()
        self.vfs = load_vfs(self.archive(self.ENTRIES))
        self.session = Session(vfs=self.vfs)

    def run_line(self, line):
        """Выполнить команду в текущем сеансе."""
        return execute(line, self.session)
