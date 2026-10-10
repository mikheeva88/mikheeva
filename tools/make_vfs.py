"""Генератор тестовых VFS-архивов (ZIP) для проверки эмулятора.

Запуск: python tools/make_vfs.py [ПАПКА]   (по умолчанию vfs_data).

Архивы создаются заново при каждом запуске и в репозитории не
хранятся (папка vfs_data игнорируется git).
"""

import os
import sys
import zipfile
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_DIR = "vfs_data"
BROKEN_NAME = "broken.zip"
BROKEN_TEXT = "Это обычный текст, а не ZIP-архив.\n"
BINARY_DATA = bytes(
    [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0xFF, 0xFE, 0x00, 0x01]
)

Entry = Tuple[str, bytes]

ARCHIVES: Dict[str, List[Entry]] = {
    "minimal.zip": [
        ("hello.txt", "Привет из VFS!\n".encode("utf-8")),
    ],
    "several.zip": [
        ("readme.txt", "Первая строка\nВторая строка\n".encode("utf-8")),
        ("notes.txt", "Заметки\n".encode("utf-8")),
        ("empty.txt", b""),
        ("logo.bin", BINARY_DATA),
        ("docs/", b""),
        ("docs/guide.txt", "Руководство\n".encode("utf-8")),
    ],
    "deep.zip": [
        ("readme.txt", "Корневой файл VFS\n".encode("utf-8")),
        ("home/", b""),
        ("home/user/", b""),
        ("home/user/notes.txt", "Заметки пользователя\n".encode("utf-8")),
        ("home/user/docs/", b""),
        ("home/user/docs/report.txt", "Отчёт\nСтрока 2\n".encode("utf-8")),
        ("home/user/docs/отчёт.txt", "Русское имя файла\n".encode("utf-8")),
        ("home/user/docs/archive/old.txt", "Старый файл\n".encode("utf-8")),
        ("home/guest/", b""),
        ("etc/config.txt", "debug=true\n".encode("utf-8")),
        ("etc/blob.bin", BINARY_DATA),
    ],
    "traversal.zip": [
        ("../evil.txt", b"outside of the root"),
    ],
}


def write_zip(path: str, entries: Sequence[Entry]) -> None:
    """Создать ZIP-архив с заданными записями.

    Args:
        path: путь к создаваемому архиву.
        entries: пары (имя записи, содержимое); имя с «/» на конце
            означает каталог.
    """
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            archive.writestr(name, data)


def write_broken(path: str) -> None:
    """Создать файл с расширением .zip, который не является архивом."""
    with open(path, "w", encoding="utf-8") as broken_file:
        broken_file.write(BROKEN_TEXT)


def build_all(output_dir: str) -> List[str]:
    """Создать все тестовые архивы в указанной папке.

    Args:
        output_dir: папка для архивов (создаётся при необходимости).

    Returns:
        Список путей к созданным файлам.
    """
    os.makedirs(output_dir, exist_ok=True)
    created = []
    for name, entries in ARCHIVES.items():
        path = os.path.join(output_dir, name)
        write_zip(path, entries)
        created.append(path)
    broken_path = os.path.join(output_dir, BROKEN_NAME)
    write_broken(broken_path)
    created.append(broken_path)
    return created


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Создать архивы и вывести список созданных файлов."""
    args = sys.argv[1:] if argv is None else argv
    output_dir = args[0] if args else DEFAULT_DIR
    for path in build_all(output_dir):
        print(f"создан: {path}")


if __name__ == "__main__":
    main()
