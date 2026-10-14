import os
import sys
import zipfile

BINARY = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0xFF, 0xFE])
ARCHIVES = {
    "minimal.zip": [
        ("hello.txt", "Привет из VFS!\n"),
    ],
    "several.zip": [
        ("readme.txt", "Первая строка\nВторая строка\n"),
        ("notes.txt", "Заметки\n"),
        ("empty.txt", ""),
        ("logo.bin", BINARY),
        ("docs/", ""),
        ("docs/guide.txt", "Руководство\n"),
    ],
    "deep.zip": [
        ("readme.txt", "Корневой файл VFS\n"),
        ("home/", ""),
        ("home/user/", ""),
        ("home/user/notes.txt", "Заметки пользователя\n"),
        ("home/user/.profile", "export A=1\n"),
        ("home/user/docs/", ""),
        ("home/user/docs/report.txt", "Отчёт\nСтрока 2\n"),
        ("home/user/docs/отчёт.txt", "Русское имя файла\n"),
        ("home/user/docs/archive/old.txt", "Старый файл\n"),
        ("home/guest/", ""),
        ("tmp/a/", ""),
        ("tmp/b/", ""),
        ("etc/config.txt", "debug=true\n"),
        ("etc/blob.bin", BINARY),
        ("etc/lines.txt", "one\ntwo\n\nfour"),
    ],
    "traversal.zip": [
        ("../evil.txt", "outside of the root"),
    ],
}


def main():
    folder = sys.argv[1] if sys.argv[1:] else "vfs_data"
    os.makedirs(folder, exist_ok=True)
    for name, entries in ARCHIVES.items():
        with zipfile.ZipFile(os.path.join(folder, name), "w") as archive:
            for entry, data in entries:
                archive.writestr(entry, data)
    broken = os.path.join(folder, "broken.zip")
    with open(broken, "w", encoding="utf-8") as broken_file:
        broken_file.write("Это обычный текст, а не ZIP-архив\n")
    print(f"архивы созданы в папке {folder}")


if __name__ == "__main__":
    main()
