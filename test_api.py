"""Тест всех файлов по одному"""
import time
import requests
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
TEST_FILES_DIR = Path("test_files")


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️ {msg}{Colors.RESET}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️ {msg}{Colors.RESET}")


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")


def check_server() -> bool:
    """Проверяем, запущен ли сервер"""
    print_info("Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_success("Server is running")
            return True
    except requests.exceptions.ConnectionError:
        print_error("Server is not running")
        print_info("Start server with: uvicorn app.main:app --reload")
        return False
    return False


def get_file_size_mb(file_path: Path) -> float:
    """Возвращает размер файла в MB"""
    return file_path.stat().st_size / (1024 * 1024)


def test_file(file_path: Path) -> bool:
    """Тестируем один файл"""
    print(f"\n📁 Testing: {file_path.name}")

    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print_info(f"File size: {size_mb:.2f} MB")

    # Определяем таймауты
    if size_mb < 10:
        upload_timeout = 60
        process_timeout = 300
        check_interval = 2
    elif size_mb < 100:
        upload_timeout = 180
        process_timeout = 600
        check_interval = 3
    elif size_mb < 500:
        upload_timeout = 300
        process_timeout = 1800
        check_interval = 5
    else:
        upload_timeout = 600
        process_timeout = 3600
        check_interval = 10

    try:
        # 1. Загружаем файл
        print_info(f"Uploading...")
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/public/report/export",
                files={'file': f},
                timeout=upload_timeout
            )

        if response.status_code != 202:
            print_error(f"Upload failed: {response.status_code}")
            return False

        task = response.json()
        task_id = task['task_id']
        print_success(f"Task created: {task_id}")

        # 2. Ждём завершения обработки
        print_info(f"Processing...")
        start_time = time.time()

        while time.time() - start_time < process_timeout:
            try:
                status_resp = requests.get(
                    f"{BASE_URL}/public/report/{task_id}/status",
                    timeout=30
                )

                if status_resp.status_code == 200:
                    status = status_resp.json()
                    print(f"   Status: {status['status']} ({status['progress']}%)")

                    if status['status'] == 'completed':
                        print_success("Processing completed!")
                        break
                    elif status['status'] == 'failed':
                        print_error(f"Processing failed: {status.get('error', 'Unknown error')}")
                        return False
            except Exception as e:
                print_warning(f"Status check error: {e}")

            time.sleep(check_interval)
        else:
            print_error(f"Timeout after {process_timeout}s")
            return False

        # 3. ПРОВЕРЯЕМ что файл существует (НЕ СКАЧИВАЕМ!)
        result_filename = f"{task_id}_{task['file_name']}_analysis.xlsx"
        result_path = Path("results") / result_filename

        if result_path.exists():
            result_size = result_path.stat().st_size / 1024
            print_success(f"Result file exists: {result_path.name} ({result_size:.2f} KB)")
            return True
        else:
            print_warning(f"Result file not found: {result_path}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_queue_status():
    """Проверяем статус очереди"""
    try:
        response = requests.get(
            f"{BASE_URL}/public/report/queue/status",
            timeout=10
        )

        if response.status_code == 200:
            status = response.json()
            print_info(f"Queue: {status.get('queue_size', '?')}/{status.get('max_queue_size', '?')}")
            print_info(f"Active tasks: {status.get('active_tasks', '?')}")
            print_info(f"Total tasks: {status.get('total_tasks', '?')}")
            return True
        else:
            print_warning(f"Queue status endpoint returned {response.status_code}")
            return False

    except Exception as e:
        print_warning(f"Queue status check failed: {e}")
        return False


def get_files_sorted_by_size() -> list[Path]:
    """Возвращает список файлов, отсортированный по размеру (от меньшего к большему)"""
    if not TEST_FILES_DIR.exists():
        return []

    all_files = [f for f in TEST_FILES_DIR.glob("*") if f.is_file()]
    # Сортируем по размеру файла
    all_files.sort(key=lambda f: f.stat().st_size)
    return all_files


def main():
    """Основная функция"""
    print_header("WORD ANALYZER - TEST ALL FILES (optimized for large files)")

    if not check_server():
        return

    if not TEST_FILES_DIR.exists():
        print_error(f"Test files directory not found: {TEST_FILES_DIR}")
        print_info("Run: python scripts/generate_test_files.py")
        return

    # Получаем файлы, отсортированные от меньшего к большему
    all_files = get_files_sorted_by_size()

    if not all_files:
        print_error("No test files found")
        print_info("Run: python scripts/generate_test_files.py")
        return

    # Показываем список файлов с размерами
    print_info(f"Found {len(all_files)} test files (sorted by size):")
    for f in all_files:
        size_mb = get_file_size_mb(f)
        print(f"   - {f.name}: {size_mb:.2f} MB")

    print_header("Initial Queue Status")
    test_queue_status()

    print_header("Running Tests (small to large)")

    results = {}
    total = len(all_files)
    passed = 0
    failed = 0
    total_start_time = time.time()

    for i, file_path in enumerate(all_files, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{total} - {file_path.name}")
        print(f"{'='*60}")

        file_start_time = time.time()
        success = test_file(file_path)
        file_elapsed = time.time() - file_start_time

        results[file_path.name] = success

        if success:
            passed += 1
            print_success(f"Completed in {file_elapsed:.1f}s")
        else:
            failed += 1
            print_error(f"Failed after {file_elapsed:.1f}s")

        # Пауза между файлами, чтобы сервер мог обработать очередь
        if i < total:
            wait_time = 2 if file_path.stat().st_size < 100 * 1024 * 1024 else 5
            print_info(f"Waiting {wait_time}s before next file...")
            time.sleep(wait_time)

    total_elapsed = time.time() - total_start_time

    print_header("Final Queue Status")
    test_queue_status()

    # Выводим итоговый отчёт
    print_header("TEST SUMMARY")

    print(f"\nTotal files: {total}")
    print(f"Total time: {total_elapsed / 60:.1f} minutes")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")

    print("\n📋 Detailed results:")
    for name, success in results.items():
        if success:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}")

    print_header("Results Location")
    print_info("Excel files saved to: test_results/")

    results_dir = Path("test_results")
    if results_dir.exists():
        result_files = list(results_dir.glob("*.xlsx"))
        if result_files:
            print(f"\nGenerated {len(result_files)} result files:")
            total_size = 0
            for rf in sorted(result_files):
                size_kb = rf.stat().st_size / 1024
                total_size += size_kb
                print(f"  - {rf.name} ({size_kb:.2f} KB)")
            print(f"\n  Total results size: {total_size / 1024:.2f} MB")

    print_header("DONE")


if __name__ == "__main__":
    main()