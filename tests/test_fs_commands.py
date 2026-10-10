"""Тесты команд ls и cd."""

import unittest

from zip_helper import SessionTestCase

ENTRIES = [
    ("a.txt", b"12345"),
    ("B.txt", b"b"),
    (".hidden", b"h"),
    ("docs/", b""),
    ("docs/guide.txt", b"guide"),
    ("docs/deep/x.txt", b"x"),
    ("void/", b""),
]


class TestLs(SessionTestCase):
    """Проверка команды ls."""

    ENTRIES = ENTRIES

    def test_default(self):
        """Без аргументов: текущий каталог, скрытые не показываются."""
        result = self.run_line("ls")
        self.assertEqual(result.output, "a.txt  B.txt  docs  void")
        self.assertFalse(result.is_error)

    def test_path(self):
        """С путём: содержимое указанного каталога."""
        self.assertEqual(self.run_line("ls docs").output, "deep  guide.txt")
        self.assertEqual(self.run_line("ls /docs/deep").output, "x.txt")

    def test_empty_dir(self):
        """Пустой каталог даёт пустой вывод."""
        self.assertEqual(self.run_line("ls void").output, "")

    def test_all(self):
        """Ключ -a добавляет «.», «..» и скрытые файлы."""
        result = self.run_line("ls -a")
        self.assertEqual(
            result.output, ".  ..  .hidden  a.txt  B.txt  docs  void"
        )

    def test_long(self):
        """Ключ -l: тип, размер и имя по строке на запись."""
        lines = self.run_line("ls -l docs").output.split("\n")
        self.assertEqual(lines[0], f"d {0:>8} deep")
        self.assertEqual(lines[1], f"- {5:>8} guide.txt")

    def test_combined_flags(self):
        """Ключи можно объединять: -la и -al."""
        first = self.run_line("ls -la").output
        second = self.run_line("ls -al").output
        self.assertEqual(first, second)
        self.assertIn(f"- {1:>8} .hidden", first)

    def test_file(self):
        """Для файла выводится его имя (путь как указан)."""
        self.assertEqual(self.run_line("ls docs/guide.txt").output,
                         "docs/guide.txt")

    def test_several_paths(self):
        """Несколько путей: файлы первыми, у каталогов заголовки."""
        result = self.run_line("ls docs a.txt void")
        expected = "a.txt\n\ndocs:\ndeep  guide.txt\n\nvoid:\n"
        self.assertEqual(result.output, expected)

    def test_relative_to_cwd(self):
        """Путь считается от текущего каталога."""
        self.run_line("cd docs")
        self.assertEqual(self.run_line("ls").output, "deep  guide.txt")
        self.assertEqual(self.run_line("ls ..").output,
                         "a.txt  B.txt  docs  void")

    def test_missing_path(self):
        """Несуществующий путь — только ошибка."""
        result = self.run_line("ls docs nope")
        self.assertTrue(result.is_error)
        self.assertEqual(result.output,
                         "ls: nope: нет такого файла или каталога")

    def test_unknown_option(self):
        """Неизвестный ключ — ошибка."""
        result = self.run_line("ls -z")
        self.assertTrue(result.is_error)
        self.assertIn("'z'", result.output)

    def test_without_vfs(self):
        """Без VFS ls сообщает об ошибке."""
        self.session.vfs = None
        self.assertTrue(self.run_line("ls").is_error)


class TestCd(SessionTestCase):
    """Проверка команды cd."""

    ENTRIES = ENTRIES

    def test_relative_and_absolute(self):
        """Переход по относительному и абсолютному пути."""
        self.run_line("cd docs/deep")
        self.assertEqual(self.session.cwd, "/docs/deep")
        self.run_line("cd /void")
        self.assertEqual(self.session.cwd, "/void")

    def test_parent(self):
        """«..» поднимает на уровень выше, в корне остаётся корень."""
        self.run_line("cd docs/deep")
        self.run_line("cd ../..")
        self.assertEqual(self.session.cwd, "/")
        self.run_line("cd ..")
        self.assertEqual(self.session.cwd, "/")

    def test_dots_in_path(self):
        """Путь с «.» и «..» посередине."""
        self.run_line("cd docs/deep/../../void/.")
        self.assertEqual(self.session.cwd, "/void")

    def test_no_args(self):
        """cd без аргументов переходит в корень."""
        self.run_line("cd docs")
        self.assertEqual(self.run_line("cd").output, "")
        self.assertEqual(self.session.cwd, "/")

    def test_previous(self):
        """cd - возвращает в прошлый каталог и выводит его."""
        self.run_line("cd docs")
        self.run_line("cd deep")
        result = self.run_line("cd -")
        self.assertEqual(result.output, "/docs")
        self.assertEqual(self.session.cwd, "/docs")
        self.assertEqual(self.session.prev_cwd, "/docs/deep")

    def test_normal_cd_prints_nothing(self):
        """Обычный cd ничего не выводит."""
        self.assertEqual(self.run_line("cd docs").output, "")

    def test_missing(self):
        """Несуществующий каталог — ошибка, каталог не меняется."""
        result = self.run_line("cd nope")
        self.assertTrue(result.is_error)
        self.assertEqual(self.session.cwd, "/")

    def test_file(self):
        """cd в файл — ошибка «не каталог»."""
        result = self.run_line("cd a.txt")
        self.assertTrue(result.is_error)
        self.assertIn("не каталог", result.output)

    def test_too_many_args(self):
        """Два аргумента — ошибка."""
        result = self.run_line("cd docs void")
        self.assertEqual(result.output, "cd: слишком много аргументов")
        self.assertEqual(self.session.cwd, "/")

    def test_without_vfs(self):
        """Без VFS cd сообщает об ошибке."""
        self.session.vfs = None
        self.assertTrue(self.run_line("cd").is_error)


if __name__ == "__main__":
    unittest.main()
