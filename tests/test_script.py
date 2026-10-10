"""Тесты загрузки и выполнения стартового скрипта."""

import os
import tempfile
import unittest

from emulator.script import (
    ScriptError,
    is_skipped,
    iter_commands,
    load_script,
    run_script,
)
from emulator.session import Session
from emulator.vfs import load_vfs
from zip_helper import make_zip

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "examples")


def example_path(name):
    """Вернуть путь к примеру стартового скрипта из папки examples."""
    return os.path.join(EXAMPLES_DIR, name)


def errors_of(results):
    """Вернуть строки, выполнение которых закончилось ошибкой."""
    return [line for line, result in results if result.is_error]


class TestLoadScript(unittest.TestCase):
    """Проверка чтения файла скрипта."""

    def write_file(self, content, encoding="utf-8"):
        """Создать временный файл и вернуть путь к нему."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = os.path.join(folder.name, "script.txt")
        with open(path, "w", encoding=encoding, newline="") as file:
            file.write(content)
        return path

    def test_lines(self):
        """Строки читаются без символов перевода строки."""
        path = self.write_file("ls\r\ncd a\nexit\n")
        self.assertEqual(load_script(path), ["ls", "cd a", "exit"])

    def test_bom(self):
        """BOM в начале файла (Блокнот Windows) отбрасывается."""
        path = self.write_file("ls\n", encoding="utf-8-sig")
        self.assertEqual(load_script(path), ["ls"])

    def test_missing_file(self):
        """Несуществующий файл даёт ScriptError."""
        with self.assertRaises(ScriptError):
            load_script(os.path.join(EXAMPLES_DIR, "no_such_file.txt"))

    def test_directory(self):
        """Папка вместо файла даёт ScriptError."""
        with self.assertRaises(ScriptError):
            load_script(EXAMPLES_DIR)


class TestIsSkipped(unittest.TestCase):
    """Проверка пропуска пустых строк и комментариев."""

    def test_skipped(self):
        """Пустые строки и комментарии пропускаются."""
        for line in ["", "   ", "\t", "# comment", "   # comment"]:
            self.assertTrue(is_skipped(line), repr(line))

    def test_not_skipped(self):
        """Команды не пропускаются."""
        for line in ["ls", "  cd a", "foo"]:
            self.assertFalse(is_skipped(line), repr(line))


class TestIterCommands(unittest.TestCase):
    """Проверка выбора команд из строк скрипта."""

    def test_filter(self):
        """Пустые строки и комментарии отбрасываются, пробелы убираются."""
        lines = ["# c", "", " echo a ", "  ", "ls"]
        self.assertEqual(list(iter_commands(lines)), ["echo a", "ls"])


class TestRunScript(unittest.TestCase):
    """Проверка выполнения строк скрипта."""

    def test_order_and_echo(self):
        """Строки выполняются по порядку, пробелы по краям убираются."""
        results = list(run_script(["  echo a  ", "# note", "", "echo b"]))
        self.assertEqual([line for line, _ in results],
                         ["echo a", "echo b"])
        self.assertEqual(results[0][1].output, "a")
        self.assertEqual(results[1][1].output, "b")

    def test_errors_do_not_stop(self):
        """Ошибочные строки не прерывают выполнение."""
        results = list(run_script(["foo", "echo", "exit now", "echo a"]))
        self.assertEqual(errors_of(results), ["foo", "exit now"])
        self.assertEqual(len(results), 4)

    def test_vfs_is_passed(self):
        """Команды скрипта получают загруженную VFS."""
        vfs = load_vfs(self.make_archive())
        results = list(run_script(["vfs-info"], Session(vfs=vfs)))
        self.assertFalse(results[0][1].is_error)

    def test_cwd_is_kept_between_lines(self):
        """Текущий каталог сохраняется между строками скрипта."""
        vfs = load_vfs(self.make_archive())
        lines = ["cd /", "ls"]
        results = list(run_script(lines, Session(vfs=vfs)))
        self.assertEqual(results[1][1].output, "a.txt")

    def make_archive(self):
        """Создать маленький архив во временной папке."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = os.path.join(folder.name, "a.zip")
        make_zip(path, [("a.txt", b"1")])
        return path

    def test_exit_stops(self):
        """После exit остальные строки не выполняются."""
        results = list(run_script(["echo", "exit", "echo a"]))
        self.assertEqual([line for line, _ in results], ["echo", "exit"])
        self.assertTrue(results[-1][1].should_exit)


class TestExamples(unittest.TestCase):
    """Проверка примеров скриптов из папки examples."""

    def run_example(self, name):
        """Выполнить пример скрипта и вернуть результаты."""
        return list(run_script(load_script(example_path(name))))

    def test_basic(self):
        """В basic.txt нет ошибок (VFS не нужна)."""
        results = self.run_example("basic.txt")
        self.assertEqual(errors_of(results), [])
        self.assertFalse(results[-1][1].should_exit)

    def test_with_errors(self):
        """В with_errors.txt три ошибки, а скрипт доходит до конца."""
        results = self.run_example("with_errors.txt")
        expected = ["foo bar", "exit now", "unknown_command"]
        self.assertEqual(errors_of(results), expected)
        self.assertEqual(results[-1][0], "echo fourth")

    def test_with_exit(self):
        """В with_exit.txt выполнение останавливается на exit."""
        results = self.run_example("with_exit.txt")
        self.assertEqual(results[-1][0], "exit")
        self.assertTrue(results[-1][1].should_exit)


if __name__ == "__main__":
    unittest.main()
