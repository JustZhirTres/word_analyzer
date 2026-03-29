import random
from pathlib import Path

WORDS = [
    "привет", "мир", "программирование", "python", "fastapi",
    "алгоритм", "данные", "сервер", "очередь", "обработка",
    "анализ", "текст", "слово", "частота", "статистика"
]

FILE_SIZES = {
    "tiny": 10,        # 10 строк
    "small": 100,      # 100 строк
    "medium": 1000,    # 1000 строк
    "large": 10000,    # 10000 строк
    "huge": 100000,    # 100000 строк (~10MB)
    "gigabyte": 20000000,  # 10 млн строк (~500MB)
}


def generate_txt_file(filepath: str, num_lines: int) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            line_words_count = random.randint(1, 10)
            line_words = random.choices(WORDS, k=line_words_count)
            f.write(' '.join(line_words))
            if i < num_lines - 1:
                f.write('\n')


def main():
    base_dir = Path(__file__).parent.parent
    test_files_dir = base_dir / "test_files"
    test_files_dir.mkdir(exist_ok=True)

    print("Generating test TXT files...")

    for size_name, num_lines in FILE_SIZES.items():
        filepath = test_files_dir / f"test_{size_name}.txt"
        print(f"  Creating {filepath.name} ({num_lines} lines)...")
        generate_txt_file(str(filepath), num_lines)

        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"    Done! Size: {size_mb:.2f} MB")

    print("\n✅ Test files generated in test_files/")


if __name__ == "__main__":
    main()