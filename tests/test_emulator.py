"""Модульные тесты эмулятора."""

import base64
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

import emulator

ROOT_DIR = os.path.join(os.path.dirname(__file__), os.pardir)
TOOL_PATH = os.path.join(ROOT_DIR, "tools", "make_vfs.py")
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")
BINARY = bytes([0x89, 0x50, 0x0A, 0xFF, 0x00, 0x0A, 0x01])
ENTRIES = [
    ("a.txt", b"12345"),
    ("two.txt", b"first\nsecond\n"),
    ("no_newline.txt", b"a\nb"),
    ("blank.txt", b"x\n\ny\n"),
    ("empty.txt", b""),
    ("bin.dat", BINARY),
    ("docs/", b""),
    ("docs/guide.txt", b"guide"),
    ("docs/deep/x.txt", b"x"),
    ("void/", b""),
]


def make_zip(path, entries):
    """Создать ZIP-архив по списку пар (имя записи, содержимое)."""
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries:
            archive.writestr(name, data)


class ArchiveTestCase(unittest.TestCase):
    """Базовый класс: временная папка и создание архивов."""

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

    def shell(self, entries=ENTRIES):
        """Создать оболочку с VFS из архива."""
        return emulator.Shell(emulator.load_vfs(self.archive(entries)))


class TestLoadVfs(ArchiveTestCase):
    """Загрузка VFS из ZIP-архива."""

    def test_tree(self):
        """Каталоги это словари, файлы это байты, неявные каталоги есть."""
        vfs = emulator.load_vfs(self.archive(ENTRIES))
        self.assertEqual(vfs["a.txt"], b"12345")
        self.assertEqual(vfs["docs"]["deep"]["x.txt"], b"x")
        self.assertEqual(vfs["void"], {})

    def test_empty_archive(self):
        """Пустой архив даёт пустую VFS."""
        self.assertEqual(emulator.load_vfs(self.archive([])), {})

    def test_nothing_written_to_disk(self):
        """Загрузка ничего не распаковывает на диск."""
        path = self.archive(ENTRIES)
        emulator.load_vfs(path)
        self.assertEqual(os.listdir(self.folder), ["test.zip"])

    def test_unicode_names(self):
        """Имена с кириллицей читаются правильно."""
        path = self.archive([("папка/файл.txt", "текст".encode("utf-8"))])
        vfs = emulator.load_vfs(path)
        self.assertEqual(vfs["папка"]["файл.txt"].decode("utf-8"), "текст")

    def test_missing_file(self):
        """Несуществующий архив."""
        with self.assertRaises(emulator.VfsError):
            emulator.load_vfs(os.path.join(self.folder, "no.zip"))

    def test_not_a_zip(self):
        """Файл, не являющийся архивом."""
        path = os.path.join(self.folder, "fake.zip")
        with open(path, "w", encoding="utf-8") as fake:
            fake.write("not a zip")
        with self.assertRaises(emulator.VfsError):
            emulator.load_vfs(path)

    def test_directory_instead_of_file(self):
        """Папка вместо архива."""
        with self.assertRaises(emulator.VfsError):
            emulator.load_vfs(self.folder)

    def test_path_traversal(self):
        """Запись с «..» отвергается."""
        with self.assertRaises(emulator.VfsError):
            emulator.load_vfs(self.archive([("../evil.txt", b"x")]))

    def test_name_conflict(self):
        """Файл и каталог с одним именем."""
        with self.assertRaises(emulator.VfsError):
            emulator.load_vfs(self.archive([("a", b"x"), ("a/b", b"y")]))

    def test_duplicate_file(self):
        """Две записи с одним именем."""
        with self.assertWarns(UserWarning):
            path = self.archive([("a.txt", b"1"), ("a.txt", b"2")])
        with self.assertRaises(emulator.VfsError):
            emulator.load_vfs(path)


class TestLs(ArchiveTestCase):
    """Команда ls."""

    def test_default(self):
        """Без аргументов: текущий каталог, каталоги со «/»."""
        output = self.shell().run("ls").output.split("\n")
        self.assertEqual(output[:2], ["a.txt", "bin.dat"])
        self.assertIn("docs/", output)
        self.assertIn("void/", output)

    def test_path(self):
        """С путём: содержимое указанного каталога."""
        shell = self.shell()
        self.assertEqual(shell.run("ls docs").output, "deep/\nguide.txt")
        self.assertEqual(shell.run("ls /docs/deep").output, "x.txt")

    def test_empty_dir(self):
        """Пустой каталог даёт пустой вывод."""
        self.assertEqual(self.shell().run("ls void").output, "")

    def test_file(self):
        """Для файла выводится его имя."""
        self.assertEqual(self.shell().run("ls docs/guide.txt").output,
                         "docs/guide.txt")

    def test_relative_to_cwd(self):
        """Путь считается от текущего каталога."""
        shell = self.shell()
        shell.run("cd docs")
        self.assertEqual(shell.run("ls").output, "deep/\nguide.txt")
        self.assertIn("docs/", shell.run("ls ..").output)

    def test_errors(self):
        """Нет пути и лишние аргументы."""
        shell = self.shell()
        missing = shell.run("ls nope")
        self.assertTrue(missing.is_error)
        self.assertEqual(missing.output,
                         "ls: nope: нет такого файла или каталога")
        self.assertEqual(shell.run("ls docs void").output,
                         "ls: слишком много аргументов")

    def test_empty_vfs(self):
        """Пустая VFS: ls ничего не выводит."""
        result = emulator.Shell({}).run("ls")
        self.assertEqual(result.output, "")
        self.assertFalse(result.is_error)


class TestCd(ArchiveTestCase):
    """Команда cd."""

    def test_relative_and_absolute(self):
        """Переход по относительному и абсолютному пути."""
        shell = self.shell()
        shell.run("cd docs/deep")
        self.assertEqual(shell.cwd, "/docs/deep")
        shell.run("cd /void")
        self.assertEqual(shell.cwd, "/void")

    def test_parent(self):
        """«..» поднимает на уровень выше, в корне остаётся корень."""
        shell = self.shell()
        shell.run("cd docs/deep")
        shell.run("cd ../..")
        self.assertEqual(shell.cwd, "/")
        shell.run("cd ..")
        self.assertEqual(shell.cwd, "/")

    def test_dots_in_path(self):
        """Путь с «.» и «..» посередине."""
        shell = self.shell()
        shell.run("cd docs/deep/../../void/.")
        self.assertEqual(shell.cwd, "/void")

    def test_no_args(self):
        """cd без аргументов переходит в корень и ничего не выводит."""
        shell = self.shell()
        shell.run("cd docs")
        self.assertEqual(shell.run("cd").output, "")
        self.assertEqual(shell.cwd, "/")

    def test_errors(self):
        """Нет каталога, файл, лишние аргументы: каталог не меняется."""
        shell = self.shell()
        self.assertTrue(shell.run("cd nope").is_error)
        self.assertIn("не каталог", shell.run("cd a.txt").output)
        self.assertEqual(shell.run("cd docs void").output,
                         "cd: слишком много аргументов")
        self.assertEqual(shell.cwd, "/")


class TestEcho(unittest.TestCase):
    """Команда echo."""

    def test_words(self):
        """Аргументы выводятся через один пробел."""
        self.assertEqual(emulator.Shell({}).run("echo a   b  c").output,
                         "a b c")

    def test_quotes(self):
        """В кавычках пробелы сохраняются."""
        self.assertEqual(emulator.Shell({}).run('echo "a   b"').output,
                         "a   b")

    def test_no_args(self):
        """Без аргументов вывод пустой."""
        result = emulator.Shell({}).run("echo")
        self.assertEqual(result.output, "")
        self.assertFalse(result.is_error)


class TestTextHelpers(unittest.TestCase):
    """Функции reverse_lines и format_content."""

    def test_reverse_lines(self):
        """Строки идут в обратном порядке, пустые сохраняются."""
        self.assertEqual(emulator.reverse_lines(b"a\nb\nc\n"), b"c\nb\na")
        self.assertEqual(emulator.reverse_lines(b"a\nb"), b"b\na")
        self.assertEqual(emulator.reverse_lines(b"x\n\ny\n"), b"y\n\nx")
        self.assertEqual(emulator.reverse_lines(b""), b"")

    def test_text_content(self):
        """Текст выводится как есть."""
        data = "Привет\r\nмир\n".encode("utf-8")
        self.assertEqual(emulator.format_content(data), "Привет\nмир")

    def test_binary_content(self):
        """Двоичные данные выводятся в base64."""
        header, encoded = emulator.format_content(BINARY).split("\n")
        self.assertIn("base64", header)
        self.assertEqual(base64.b64decode(encoded), BINARY)


class TestTac(ArchiveTestCase):
    """Команда tac."""

    def test_single_file(self):
        """Строки файла выводятся с конца."""
        self.assertEqual(self.shell().run("tac two.txt").output,
                         "second\nfirst")

    def test_no_trailing_newline(self):
        """Файл без завершающего перевода строки."""
        self.assertEqual(self.shell().run("tac no_newline.txt").output,
                         "b\na")

    def test_blank_lines(self):
        """Пустые строки сохраняются."""
        self.assertEqual(self.shell().run("tac blank.txt").output,
                         "y\n\nx")

    def test_several_files(self):
        """Каждый файл переворачивается отдельно, в порядке аргументов."""
        output = self.shell().run("tac two.txt blank.txt").output
        self.assertEqual(output, "second\nfirst\ny\n\nx")

    def test_empty_file(self):
        """Пустой файл ничего не выводит."""
        result = self.shell().run("tac empty.txt")
        self.assertEqual(result.output, "")
        self.assertFalse(result.is_error)

    def test_binary(self):
        """Двоичный файл: строки в обратном порядке, вывод в base64."""
        output = self.shell().run("tac bin.dat").output
        expected = bytes([0x01, 0x0A, 0xFF, 0x00, 0x0A, 0x89, 0x50])
        self.assertEqual(base64.b64decode(output.split("\n")[1]), expected)

    def test_relative_path(self):
        """Путь считается от текущего каталога."""
        shell = self.shell()
        shell.run("cd docs")
        self.assertEqual(shell.run("tac guide.txt").output, "guide")
        self.assertEqual(shell.run("tac ../two.txt").output, "second\nfirst")

    def test_errors(self):
        """Нет аргументов, каталог, нет файла (вывода нет совсем)."""
        shell = self.shell()
        self.assertIn("использование", shell.run("tac").output)
        self.assertEqual(shell.run("tac docs").output,
                         "tac: docs: это каталог")
        result = shell.run("tac two.txt nope.txt")
        self.assertTrue(result.is_error)
        self.assertNotIn("second", result.output)


class TestRun(unittest.TestCase):
    """Выполнение строки: exit, ошибки ввода."""

    def test_exit(self):
        """exit просит завершить эмулятор."""
        result = emulator.Shell({}).run("exit")
        self.assertTrue(result.should_exit)
        self.assertFalse(result.is_error)

    def test_exit_with_args(self):
        """exit с аргументами: ошибка, завершения нет."""
        result = emulator.Shell({}).run("exit now")
        self.assertEqual(result.output, "exit: слишком много аргументов")
        self.assertFalse(result.should_exit)

    def test_unknown_command(self):
        """Неизвестная команда."""
        result = emulator.Shell({}).run("foo bar")
        self.assertTrue(result.is_error)
        self.assertEqual(result.output, "foo: команда не найдена")

    def test_empty_input(self):
        """Пустой ввод ничего не делает."""
        for line in ["", "   \t "]:
            result = emulator.Shell({}).run(line)
            self.assertEqual(result, emulator.Result(""))

    def test_unclosed_quote(self):
        """Незакрытая кавычка: синтаксическая ошибка."""
        result = emulator.Shell({}).run('echo "abc')
        self.assertTrue(result.is_error)
        self.assertIn("синтаксическая ошибка", result.output)


class TestScript(ArchiveTestCase):
    """Чтение стартового скрипта."""

    def write(self, content, encoding="utf-8"):
        """Записать файл во временную папку и вернуть путь."""
        path = os.path.join(self.folder, "script.txt")
        with open(path, "w", encoding=encoding, newline="") as script_file:
            script_file.write(content)
        return path

    def test_read(self):
        """Строки читаются без символов перевода строки."""
        path = self.write("ls\r\ncd a\nexit\n")
        self.assertEqual(emulator.read_script(path), ["ls", "cd a", "exit"])

    def test_bom(self):
        """BOM в начале файла (Блокнот Windows) отбрасывается."""
        path = self.write("ls\n", encoding="utf-8-sig")
        self.assertEqual(emulator.read_script(path), ["ls"])

    def test_missing_file(self):
        """Несуществующий файл или папка вместо файла."""
        with self.assertRaises(emulator.ScriptError):
            emulator.read_script(os.path.join(self.folder, "no.txt"))
        with self.assertRaises(emulator.ScriptError):
            emulator.read_script(self.folder)

    def test_script_commands(self):
        """Пустые строки и комментарии отбрасываются."""
        lines = ["# c", "", " echo a ", "  ", "  # c", "ls"]
        self.assertEqual(emulator.script_commands(lines), ["echo a", "ls"])


class TestOptions(unittest.TestCase):
    """Параметры командной строки, заголовок, приглашение."""

    def test_defaults(self):
        """Без параметров значения не заданы."""
        args = emulator.parse_args([])
        self.assertIsNone(args.vfs)
        self.assertIsNone(args.script)

    def test_values(self):
        """Оба параметра, в любом порядке и через «=»."""
        args = emulator.parse_args(["--script", "b.txt", "--vfs", "a.zip"])
        self.assertEqual((args.vfs, args.script), ("a.zip", "b.txt"))
        args = emulator.parse_args(["--vfs=x", "--script=y"])
        self.assertEqual((args.vfs, args.script), ("x", "y"))

    def test_errors(self):
        """Неизвестный параметр, без значения, сокращение: SystemExit."""
        for argv in (["--unknown", "1"], ["--vfs"], ["--vf", "x"]):
            quiet = contextlib.redirect_stderr(io.StringIO())
            with self.assertRaises(SystemExit), quiet:
                emulator.parse_args(argv)

    def test_debug(self):
        """Отладочный вывод показывает значения или «(не задан)»."""
        text = emulator.format_debug(emulator.parse_args(["--vfs", "a.zip"]))
        self.assertIn("--vfs    = a.zip", text)
        self.assertIn("--script = (не задан)", text)

    def test_title_and_prompt(self):
        """Заголовок и приглашение с текущим каталогом."""
        self.assertEqual(emulator.format_title("alice", "pc1"),
                         "Эмулятор - [alice@pc1]")
        self.assertEqual(emulator.format_prompt("alice", "pc1", "/home"),
                         "alice@pc1:/home$")


class TestExamples(unittest.TestCase):
    """Архивы из tools/make_vfs.py и примеры скриптов из examples/."""

    @classmethod
    def setUpClass(cls):
        """Запустить генератор архивов во временную папку."""
        cls.folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.folder.cleanup)
        subprocess.run([sys.executable, TOOL_PATH, cls.folder.name],
                       check=True, capture_output=True)

    def errors_of(self, script, archive=None):
        """Выполнить пример скрипта; вернуть строки с ошибками."""
        vfs = {}
        if archive:
            vfs = emulator.load_vfs(os.path.join(self.folder.name, archive))
        shell = emulator.Shell(vfs)
        lines = emulator.read_script(os.path.join(EXAMPLES_DIR, script))
        errors = []
        for line in emulator.script_commands(lines):
            result = shell.run(line)
            if result.is_error:
                errors.append(line)
            if result.should_exit:
                break
        return errors

    def test_bad_archives(self):
        """Повреждённый архив и архив с «..» отвергаются."""
        for name in ["broken.zip", "traversal.zip"]:
            path = os.path.join(self.folder.name, name)
            with self.assertRaises(emulator.VfsError, msg=name):
                emulator.load_vfs(path)

    def test_deep_archive(self):
        """deep.zip: вложенность 5 уровней и пустой каталог."""
        path = os.path.join(self.folder.name, "deep.zip")
        vfs = emulator.load_vfs(path)
        self.assertIn("old.txt", vfs["home"]["user"]["docs"]["archive"])
        self.assertEqual(vfs["home"]["guest"], {})

    def test_basic(self):
        """basic.txt: нет ошибок и VFS не нужна."""
        self.assertEqual(self.errors_of("basic.txt"), [])

    def test_with_errors(self):
        """with_errors.txt: три ошибки, скрипт идёт до конца."""
        errors = self.errors_of("with_errors.txt")
        self.assertEqual(errors, ["foo bar", "exit now", "unknown_command"])

    def test_with_exit(self):
        """with_exit.txt: выполнение останавливается на exit."""
        self.assertEqual(self.errors_of("with_exit.txt"), [])

    def test_vfs_minimal(self):
        """vfs_minimal.txt: одна ошибка (нет файла)."""
        errors = self.errors_of("vfs_minimal.txt", "minimal.zip")
        self.assertEqual(errors, ["ls missing.txt"])

    def test_vfs_several(self):
        """vfs_several.txt: каталог, нет файла, не каталог."""
        errors = self.errors_of("vfs_several.txt", "several.zip")
        self.assertEqual(errors, ["tac docs", "tac missing.txt",
                                  "cd readme.txt"])

    def test_vfs_deep(self):
        """vfs_deep.txt: путь через файл и несуществующий каталог."""
        errors = self.errors_of("vfs_deep.txt", "deep.zip")
        self.assertEqual(errors, ["tac /etc/config.txt/extra",
                                  "cd /home/guest/nowhere"])

    def test_main_commands(self):
        """main_commands.txt (Этап 4): все режимы и ошибки."""
        errors = self.errors_of("main_commands.txt", "deep.zip")
        expected = [
            "ls /nowhere",
            "ls /home /etc",
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
        """Без VFS (пустая) в main_commands.txt больше ошибок."""
        with_vfs = self.errors_of("main_commands.txt", "deep.zip")
        without = self.errors_of("main_commands.txt")
        self.assertGreater(len(without), len(with_vfs))


if __name__ == "__main__":
    unittest.main()
