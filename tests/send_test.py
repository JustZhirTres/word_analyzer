"""
Простой тестовый скрипт для отправки файлов и получения результатов.
Запустите и выберите действие:
1. Отправить все тестовые файлы
2. Проверить статус
3. Скачать результаты
"""

import requests
import time
import os
import sys
from pathlib import Path

# Настройки
BASE_URL = "http://localhost:8000"
TEST_FILES_DIR = Path(__file__).parent / "test_files"
RESULTS_DIR = Path(__file__).parent / "results"


def print_menu():
    """Выводит меню"""
    print("\n" + "=" * 50)
    print("📊 Анализатор частоты слов")
    print("=" * 50)
    print("1. 📤 Отправить все тестовые файлы")
    print("2. 📊 Проверить статус всех задач")
    print("3. 💾 Скачать все готовые результаты")
    print("4. 🗑️  Очистить папку с результатами")
    print("5. 🚪 Выход")
    print("=" * 50)


def send_file(file_path: Path) -> dict:
    """Отправляет файл на сервер"""
    url = f"{BASE_URL}/public/report/export"

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            response = requests.post(url, files=files, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"   ❌ Ошибка {response.status_code}: {response.text}")
                return None
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None


def get_task_status(task_id: str) -> dict:
    """Получает статус задачи"""
    url = f"{BASE_URL}/public/report/status/{task_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def download_report(task_id: str, output_path: Path) -> bool:
    """Скачивает готовый отчёт"""
    url = f"{BASE_URL}/public/report/download/{task_id}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
    except:
        pass
    return False


def send_all_files():
    """Отправляет все тестовые файлы"""
    print("\n📤 Отправка файлов...")

    TEST_FILES_DIR.mkdir(exist_ok=True)

    # file2.txt
    txt_file = TEST_FILES_DIR / "file2.txt"
    if not txt_file.exists():
        print(f"   ⚠️  Файл {txt_file.name} не найден. Пожалуйста, создайте его вручную.")

    # file3.docx
    docx_file = TEST_FILES_DIR / "file3.docx"
    if not docx_file.exists():
        print(f"   ⚠️  Файл {docx_file.name} не найден. Пожалуйста, создайте его вручную.")

    # file4.pdf
    pdf_file = TEST_FILES_DIR / "file4.pdf"
    if not pdf_file.exists():
        print(f"   ⚠️  Файл {pdf_file.name} не найден. Пожалуйста, создайте его вручную.")

    # Отправляем файлы
    task_ids = {}
    for file_path in TEST_FILES_DIR.glob("*"):
        if file_path.suffix in ['.txt', '.docx', '.pdf']:
            print(f"\n   📄 {file_path.name}...")
            result = send_file(file_path)
            if result:
                task_ids[file_path.name] = result['task_id']
                print(f"      ✅ Task ID: {result['task_id'][:8]}...")
                print(f"      📊 Очередь: {result['queue_position']}")
            else:
                print(f"      ❌ Не удалось отправить")

    if task_ids:
        print(f"\n✅ Отправлено {len(task_ids)} файлов")

        # Сохраняем task_ids в файл
        import json
        tasks_file = RESULTS_DIR / "sent_tasks.json"
        RESULTS_DIR.mkdir(exist_ok=True)
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(task_ids, f, ensure_ascii=False, indent=2)
        print(f"💾 Task IDs сохранены в {tasks_file}")

    return task_ids


def check_all_status():
    """Проверяет статус всех задач"""
    import json

    tasks_file = RESULTS_DIR / "sent_tasks.json"
    if not tasks_file.exists():
        print("\n❌ Нет сохранённых задач. Сначала отправьте файлы (пункт 1)")
        return

    with open(tasks_file, 'r', encoding='utf-8') as f:
        task_ids = json.load(f)

    print("\n📊 Статус задач:")
    print("-" * 60)
    print(f"{'Файл':<20} {'Статус':<12} {'Прогресс':<10} {'Task ID':<10}")
    print("-" * 60)

    for filename, task_id in task_ids.items():
        status = get_task_status(task_id)
        if status:
            status_name = status.get('status', 'unknown')
            progress = status.get('progress', 0)

            if status_name == 'completed':
                icon = "✅"
            elif status_name == 'processing':
                icon = "🔄"
            elif status_name == 'queued':
                icon = "⏳"
            elif status_name == 'failed':
                icon = "❌"
            else:
                icon = "❓"

            print(f"{filename:<20} {icon} {status_name:<10} {progress}%      {task_id[:8]}...")
        else:
            print(f"{filename:<20} ❌ Ошибка получения статуса")

    print("-" * 60)


def download_all_results():
    """Скачивает все готовые результаты"""
    import json

    tasks_file = RESULTS_DIR / "sent_tasks.json"
    if not tasks_file.exists():
        print("\n❌ Нет сохранённых задач. Сначала отправьте файлы (пункт 1)")
        return

    with open(tasks_file, 'r', encoding='utf-8') as f:
        task_ids = json.load(f)

    RESULTS_DIR.mkdir(exist_ok=True)
    downloaded = 0

    print("\n💾 Скачивание результатов...")
    print("-" * 50)

    for filename, task_id in task_ids.items():
        status = get_task_status(task_id)

        if status and status.get('status') == 'completed':
            output_name = filename.replace('.', '_') + "_report.xlsx"
            output_path = RESULTS_DIR / output_name

            if download_report(task_id, output_path):
                print(f"   ✅ {filename} → {output_name}")
                downloaded += 1
            else:
                print(f"   ❌ {filename} — не удалось скачать")
        else:
            print(f"   ⏳ {filename} — ещё не готов (статус: {status.get('status') if status else 'unknown'})")

    print("-" * 50)
    print(f"✅ Скачано {downloaded} файлов в папку {RESULTS_DIR}")


def clear_results():
    """Очищает папку с результатами"""
    if RESULTS_DIR.exists():
        import shutil
        shutil.rmtree(RESULTS_DIR)
        RESULTS_DIR.mkdir(exist_ok=True)
        print(f"\n✅ Папка {RESULTS_DIR} очищена")
    else:
        print(f"\n⚠️ Папка {RESULTS_DIR} не существует")


def main():
    """Главное меню"""
    print("\n🔧 Запуск тестового скрипта...")
    print(f"📁 Сервер: {BASE_URL}")

    # Проверяем доступность сервера
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Сервер доступен")
    except:
        print(f"❌ Сервер недоступен! Убедитесь, что он запущен:")
        print(f"   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return

    while True:
        print_menu()
        choice = input("\nВыберите действие (1-5): ").strip()

        if choice == '1':
            send_all_files()
            input("\nНажмите Enter для продолжения...")

        elif choice == '2':
            check_all_status()
            input("\nНажмите Enter для продолжения...")

        elif choice == '3':
            download_all_results()
            input("\nНажмите Enter для продолжения...")

        elif choice == '4':
            clear_results()
            input("\nНажмите Enter для продолжения...")

        elif choice == '5':
            print("\n👋 До свидания!")
            break

        else:
            print("\n❌ Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()