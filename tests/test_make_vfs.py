"""Тесты генератора VFS-архивов и примеров скриптов к ним."""

import os
import subprocess
import sys
import tempfile
import unittest

from emulator.script import load_script, run_script
from emulator.session import Session
from emulator.vfs import VfsError, load_vfs

ROOT_DIR = os.path.join(os.path.dirname(__file__), os.pardir)
TOOL_PATH = os.path.join(ROOT_DIR, "tools", "make_vfs.py")
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")


class GeneratedArchivesTestCase(unittest.TestCase):
    """Базовый класс: архивы создаются запуском tools/make_vfs.py."""

    @classmethod
    def setUpClass(cls):
        """Запустить генератор во временную папку."""
        cls.folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.folder.cleanup)
        subprocess.run(
            [sys.executable, TOOL_PATH, cls.folder.name],
            check=True, capture_output=True,
        )

    def archive_path(self, name):
        """Вернуть путь к созданному архиву."""
        return os.path.join(self.folder.name, name)

    def load(self, name):
        """Загрузить созданный архив как VFS."""
        return load_vfs(self.archive_path(name))


class TestGeneratedArchives(GeneratedArchivesTestCase):
    """Проверка содержимого созданных архивов."""

    def test_minimal(self):
        """Минимальная VFS: один файл."""
        stats = self.load("minimal.zip").stats()
        self.assertEqual((stats.dirs, stats.files), (0, 1))

    def test_several(self):
        """Несколько файлов и один каталог."""
        vfs = self.load("several.zip")
        self.assertEqual(vfs.stats().files, 5)
        self.assertTrue(vfs.find("docs").is_dir)

    def test_deep(self):
        """Вложенность не менее трёх уровней, есть пустой каталог."""
        vfs = self.load("deep.zip")
        node = vfs.find("/home/user/docs/archive/old.txt")
        self.assertFalse(node.is_dir)
        self.assertEqual(vfs.find("/home/guest").children, {})

    def test_bad_archives(self):
        """Повреждённый архив и архив с «..» отвергаются."""
        for name in ["broken.zip", "traversal.zip"]:
            with self.assertRaises(VfsError, msg=name):
                self.load(name)


class TestExampleScripts(GeneratedArchivesTestCase):
    """Проверка примеров скриптов на соответствующих архивах."""

    def run_example(self, script, archive=None):
        """Выполнить пример скрипта; вернуть строки с ошибками."""
        session = Session(vfs=self.load(archive) if archive else None)
        lines = load_script(os.path.join(EXAMPLES_DIR, script))
        results = list(run_script(lines, session))
        return [line for line, result in results if result.is_error]

    def test_minimal_script(self):
        """vfs_minimal.txt: одна ошибка (нет файла)."""
        errors = self.run_example("vfs_minimal.txt", "minimal.zip")
        self.assertEqual(errors, ["vfs-show missing.txt"])

    def test_several_script(self):
        """vfs_several.txt: каталог и ошибки числа аргументов."""
        errors = self.run_example("vfs_several.txt", "several.zip")
        expected = [
            "vfs-show docs",
            "vfs-show",
            "vfs-show readme.txt notes.txt",
        ]
        self.assertEqual(errors, expected)

    def test_deep_script(self):
        """vfs_deep.txt: каталог и путь через файл."""
        errors = self.run_example("vfs_deep.txt", "deep.zip")
        expected = ["vfs-show /home/guest", "vfs-show /etc/config.txt/extra"]
        self.assertEqual(errors, expected)

    def test_all_commands_script(self):
        """all_commands.txt: ошибки всех видов."""
        errors = self.run_example("all_commands.txt", "deep.zip")
        expected = [
            "vfs-show missing.txt",
            "vfs-show /home",
            "vfs-show",
            "vfs-info now",
            "vfs-tree now",
            "ls /nowhere",
            "foo bar",
            "exit now",
        ]
        self.assertEqual(errors, expected)

    def test_main_commands_script(self):
        """main_commands.txt (Этап 4): все режимы и ошибки."""
        errors = self.run_example("main_commands.txt", "deep.zip")
        expected = [
            "ls -z",
            "ls /nowhere",
            "cd nowhere",
            "cd notes.txt",
            "cd /home /etc",
            "tac",
            "tac /home",
            "tac missing.txt /readme.txt",
            'echo "незакрытая кавычка',
            "foo",
            "exit now",
        ]
        self.assertEqual(errors, expected)

    def test_main_commands_without_vfs(self):
        """Без VFS ls, cd и tac в main_commands.txt дают ошибки."""
        errors = self.run_example("main_commands.txt")
        for command in ["ls", "cd", "tac"]:
            self.assertTrue(
                any(line.split()[0] == command for line in errors), command
            )

    def test_without_vfs(self):
        """Без VFS ошибкой заканчивается каждая команда vfs-*."""
        errors = self.run_example("vfs_minimal.txt")
        self.assertEqual(len(errors), 5)


if __name__ == "__main__":
    unittest.main()
