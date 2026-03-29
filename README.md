# Word Analyzer

Сервис для анализа частоты слов в текстовых файлах (TXT).

## Возможности

- Поддержка TXT файлов
- Адаптивная стратегия обработки (In-Memory для файлов до 100MB, Hybrid для файлов до 1GB, Streaming для файлов до 5GB)
- Лемматизация русских слов (pymorphy3)
- Асинхронная обработка с очередью
- Адаптивное масштабирование воркеров (от 2 до 10)
- Результат в формате Excel (три колонки: словоформа, частота в документе, частота по строкам)

## Запуск

pip install -r requirements.txt
uvicorn app.main:app --reload

## API Endpoints

POST /public/report/export — загрузка TXT файла
GET /public/report/{task_id}/status — статус обработки
GET /public/report/{task_id}/download — скачать результат
GET /public/report/queue/status — статус очереди

## Документация

- Swagger UI: \`http://localhost:8000/docs\`
- ReDoc: \`http://localhost:8000/redoc\`

## Тестирование

python scripts/generate_test_files.py
python test_all_files.py

