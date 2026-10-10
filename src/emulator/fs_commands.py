"""Команды навигации по VFS: ls и cd."""

from typing import List, Set, Tuple

from emulator.errors import CommandError
from emulator.paths import ROOT_PATH
from emulator.result import CommandResult
from emulator.session import Session
from emulator.vfs import VfsNode

OPTION_PREFIX = "-"
FLAG_LONG = "l"
FLAG_ALL = "a"
KNOWN_FLAGS = FLAG_LONG + FLAG_ALL
HIDDEN_PREFIX = "."
CURRENT_NAME = "."
PARENT_NAME = ".."
PREVIOUS_DIR = "-"
SHORT_SEPARATOR = "  "
SECTION_SEPARATOR = "\n\n"

Entry = Tuple[str, VfsNode]


def _parse_options(args: List[str]) -> Tuple[Set[str], List[str]]:
    """Разделить аргументы ls на ключи и пути.

    Args:
        args: аргументы команды.

    Returns:
        Множество ключей («l», «a») и список путей.

    Raises:
        CommandError: если указан неизвестный ключ.
    """
    flags: Set[str] = set()
    paths: List[str] = []
    for arg in args:
        if not arg.startswith(OPTION_PREFIX) or arg == OPTION_PREFIX:
            paths.append(arg)
            continue
        for char in arg[1:]:
            if char not in KNOWN_FLAGS:
                raise CommandError(f"неверный ключ -- '{char}'")
            flags.add(char)
    return flags, paths


def _name_key(name: str) -> tuple:
    """Ключ сортировки имён: без учёта регистра, затем по имени."""
    return (name.casefold(), name)


def _entry_line(name: str, node: VfsNode, long_format: bool) -> str:
    """Сформировать строку записи: имя или строка длинного формата."""
    if not long_format:
        return name
    kind = "d" if node.is_dir else "-"
    size = 0 if node.is_dir else len(node.data)
    return f"{kind} {size:>8} {name}"


def _join(lines: List[str], long_format: bool) -> str:
    """Склеить записи: по строке в длинном формате, иначе в одну."""
    separator = "\n" if long_format else SHORT_SEPARATOR
    return separator.join(lines)


def _dir_entries(node: VfsNode, show_all: bool) -> List[Entry]:
    """Вернуть записи каталога: скрытые только при show_all."""
    names = sorted(node.children, key=_name_key)
    entries = [
        (name, node.children[name]) for name in names
        if show_all or not name.startswith(HIDDEN_PREFIX)
    ]
    if show_all:
        entries = [(CURRENT_NAME, node), (PARENT_NAME, node)] + entries
    return entries


def cmd_ls(args: List[str], session: Session) -> CommandResult:
    """Команда ls [-l] [-a] [ПУТЬ...]: содержимое каталогов и файлы.

    Без пути выводится текущий каталог. Файлы выводятся первыми,
    затем каталоги (с заголовком «путь:», если путей несколько).
    Если какой-либо путь не найден, выводится только ошибка.
    """
    flags, paths = _parse_options(args)
    long_format = FLAG_LONG in flags
    targets = [
        (path, session.lookup(path)) for path in paths or [CURRENT_NAME]
    ]
    targets.sort(key=lambda item: _name_key(item[0]))
    sections = []
    files = [(path, node) for path, node in targets if not node.is_dir]
    if files:
        lines = [_entry_line(p, n, long_format) for p, n in files]
        sections.append(_join(lines, long_format))
    show_header = bool(paths[1:])
    for path, node in targets:
        if not node.is_dir:
            continue
        entries = _dir_entries(node, FLAG_ALL in flags)
        lines = [_entry_line(n, c, long_format) for n, c in entries]
        body = _join(lines, long_format)
        sections.append(f"{path}:\n{body}" if show_header else body)
    return CommandResult(SECTION_SEPARATOR.join(sections))


def _cd_target(args: List[str], session: Session) -> str:
    """Определить, куда переходить: корень, прошлый каталог или путь."""
    if not args:
        return ROOT_PATH
    if args[0] == PREVIOUS_DIR:
        return session.prev_cwd
    return args[0]


def cmd_cd(args: List[str], session: Session) -> CommandResult:
    """Команда cd [ПУТЬ | -]: сменить текущий каталог.

    Без аргументов переходит в корень VFS, «cd -» возвращает в
    предыдущий каталог и выводит его путь.
    """
    if args[1:]:
        raise CommandError("слишком много аргументов")
    target = _cd_target(args, session)
    node = session.lookup(target)
    if not node.is_dir:
        raise CommandError(f"{target}: не каталог")
    new_cwd = session.resolve(target)
    session.prev_cwd = session.cwd
    session.cwd = new_cwd
    return CommandResult(new_cwd if args == [PREVIOUS_DIR] else "")
