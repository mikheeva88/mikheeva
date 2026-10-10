"""Вспомогательные функции для тестов: создание ZIP-архивов."""

import os
import tempfile
import unittest
import zipfile


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
