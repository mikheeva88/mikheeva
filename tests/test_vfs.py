"""Тесты загрузки и устройства VFS."""

import os
import unittest

from emulator.vfs import MAX_DEPTH, VfsError, load_vfs, split_path
from zip_helper import TempDirTestCase

TREE_ENTRIES = [
    ("a.txt", b"12345"),
    ("dir/", b""),
    ("dir/b.txt", b"ab"),
    ("dir/sub/c.txt", b"c"),
    ("empty/", b""),
]


class TestSplitPath(unittest.TestCase):
    """Проверка разбиения пути."""

    def test_parts(self):
        """Лишние слеши и точки отбрасываются."""
        self.assertEqual(split_path("/a//b/./c/"), ["a", "b", "c"])

    def test_root(self):
        """Корень даёт пустой список."""
        self.assertEqual(split_path("/"), [])


class TestLoad(TempDirTestCase):
    """Проверка загрузки архива."""

    def test_files_and_dirs(self):
        """Файлы и каталоги попадают в дерево, неявные каталоги тоже."""
        vfs = load_vfs(self.archive(TREE_ENTRIES))
        self.assertEqual(vfs.find("a.txt").data, b"12345")
        self.assertTrue(vfs.find("dir/sub").is_dir)
        self.assertEqual(vfs.find("/dir/sub/c.txt").data, b"c")
        self.assertTrue(vfs.find("empty").is_dir)

    def test_stats(self):
        """Статистика считает каталоги (без корня), файлы и размер."""
        stats = load_vfs(self.archive(TREE_ENTRIES)).stats()
        self.assertEqual(stats.dirs, 3)
        self.assertEqual(stats.files, 3)
        self.assertEqual(stats.size, 8)

    def test_empty_archive(self):
        """Пустой архив даёт пустую VFS."""
        stats = load_vfs(self.archive([])).stats()
        self.assertEqual((stats.dirs, stats.files, stats.size), (0, 0, 0))

    def test_source(self):
        """VFS помнит путь к архиву."""
        path = self.archive(TREE_ENTRIES)
        self.assertEqual(load_vfs(path).source, path)

    def test_nothing_written_to_disk(self):
        """Загрузка ничего не распаковывает на диск."""
        self.archive(TREE_ENTRIES)
        before = sorted(os.listdir(self.folder))
        load_vfs(os.path.join(self.folder, "test.zip"))
        self.assertEqual(sorted(os.listdir(self.folder)), before)

    def test_unicode_names(self):
        """Имена с кириллицей читаются правильно."""
        path = self.archive([("папка/файл.txt", "текст".encode("utf-8"))])
        node = load_vfs(path).find("папка/файл.txt")
        self.assertEqual(node.data.decode("utf-8"), "текст")


class TestFind(TempDirTestCase):
    """Проверка поиска узлов."""

    def setUp(self):
        """Загрузить VFS для поиска."""
        super().setUp()
        self.vfs = load_vfs(self.archive(TREE_ENTRIES))

    def test_root(self):
        """Пути «/» и «» дают корень."""
        self.assertIs(self.vfs.find("/"), self.vfs.root)
        self.assertIs(self.vfs.find(""), self.vfs.root)

    def test_missing(self):
        """Несуществующий путь даёт None."""
        self.assertIsNone(self.vfs.find("nope"))
        self.assertIsNone(self.vfs.find("dir/nope"))

    def test_through_file(self):
        """Путь «через файл» даёт None."""
        self.assertIsNone(self.vfs.find("a.txt/x"))

    def test_parent_reference(self):
        """Ссылка «..» не поддерживается и даёт None."""
        self.assertIsNone(self.vfs.find("dir/../a.txt"))


class TestLoadErrors(TempDirTestCase):
    """Проверка обработки ошибок загрузки."""

    def test_missing_file(self):
        """Несуществующий архив."""
        with self.assertRaises(VfsError):
            load_vfs(os.path.join(self.folder, "no.zip"))

    def test_not_a_zip(self):
        """Файл, не являющийся архивом."""
        path = os.path.join(self.folder, "fake.zip")
        with open(path, "w", encoding="utf-8") as fake:
            fake.write("not a zip")
        with self.assertRaises(VfsError):
            load_vfs(path)

    def test_directory(self):
        """Папка вместо архива."""
        with self.assertRaises(VfsError):
            load_vfs(self.folder)

    def test_path_traversal(self):
        """Запись с «..» отвергается."""
        with self.assertRaises(VfsError):
            load_vfs(self.archive([("../evil.txt", b"x")]))

    def test_file_dir_conflict(self):
        """Файл и каталог с одним именем."""
        with self.assertRaises(VfsError):
            load_vfs(self.archive([("a", b"x"), ("a/b.txt", b"y")]))

    def test_duplicate_file(self):
        """Две записи с одним именем."""
        entries = [("a.txt", b"1"), ("a.txt", b"2")]
        with self.assertWarns(UserWarning):
            path = self.archive(entries)
        with self.assertRaises(VfsError):
            load_vfs(path)

    def test_too_deep(self):
        """Слишком глубокая вложенность."""
        name = "/".join(["d"] * (MAX_DEPTH + 1)) + "/f.txt"
        with self.assertRaises(VfsError):
            load_vfs(self.archive([(name, b"x")]))


if __name__ == "__main__":
    unittest.main()
