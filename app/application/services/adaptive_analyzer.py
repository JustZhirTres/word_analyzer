import os
import sqlite3
from collections import defaultdict, Counter
import json
from tempfile import NamedTemporaryFile

from ...infrastructure.logger import logger


class AdaptiveWordAnalyzer:
    """
    Адаптивный анализатор, выбирающий стратегию в зависимости от размера файла.
    """

    def __init__(self, temp_stats_dir: str):
        self.temp_stats_dir = temp_stats_dir
        os.makedirs(temp_stats_dir, exist_ok=True)

    async def analyze_file(self, file_path: str, task_id: str, normalizer) -> list[dict]:
        """
        Анализ файла с выбором оптимальной стратегии.
        """
        file_size = os.path.getsize(file_path)

        logger.info(f"Task {task_id}: file size = {file_size / (1024 * 1024):.2f} MB")

        if file_size < 100 * 1024 * 1024: # 100 mb
            logger.info(f"Task {task_id}: using IN-MEMORY strategy")
            return await self._process_in_memory(file_path, normalizer)
        elif file_size < 1024 * 1024 * 1024: # 1gb
            logger.info(f"Task {task_id}: using HYBRID strategy")
            return await self._process_hybrid(file_path, normalizer, task_id)
        else:
            logger.info(f"Task {task_id}: using STREAMING strategy")
            return await self._process_streaming(file_path, normalizer, task_id)

    # ========== СТРАТЕГИЯ 1: In-Memory (для файлов < 100MB) ==========

    async def _process_in_memory(self, file_path: str, normalizer) -> list[dict]:
        """
        Классическая обработка в памяти. Быстро для маленьких файлов.
        Память: ~2-3x от размера файла
        """
        total_stats: dict[str, int] = defaultdict(int)
        line_stats: dict[str, list[int]] = defaultdict(list)

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if line:
                    words = normalizer.normalize(line)
                    word_counts = Counter(words)

                    for word, count in word_counts.items():
                        total_stats[word] += count

                        while len(line_stats[word]) <= line_idx:
                            line_stats[word].append(0)
                        line_stats[word][line_idx] += count

        results = []
        for word, total in sorted(total_stats.items(), key=lambda x: x[1], reverse=True):
            results.append({
                'word': word,
                'total_count': total,
                'line_counts': line_stats.get(word, [])
            })

        return results

    # ========== СТРАТЕГИЯ 2: Hybrid (для файлов 100MB - 1GB) ==========

    async def _process_hybrid(self, file_path: str, normalizer, task_id: str) -> list[dict]:
        """
        Гибридный подход: храним словарь в памяти, но периодически сбрасываем на диск.
        Память: ~500MB максимум
        """
        temp_file = NamedTemporaryFile(mode='w', suffix='.json', dir=self.temp_stats_dir, delete=False)
        temp_path = temp_file.name

        total_stats: dict[str, int] = defaultdict(int)
        line_stats: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

        lines_processed = 0
        FLUSH_INTERVAL = 50000  # Сбрасываем каждые 50000 строк

        try:
            with open(file_path, 'r', encoding='utf-8') as f, open(temp_path, 'w') as tmp:
                for line_idx, line in enumerate(f):
                    line = line.strip()
                    if line:
                        words = normalizer.normalize(line)
                        word_counts = Counter(words)

                        for word, count in word_counts.items():
                            total_stats[word] += count
                            line_stats[word][line_idx] += count

                    lines_processed += 1

                    # Периодически сбрасываем на диск, чтобы освободить память
                    if lines_processed % FLUSH_INTERVAL == 0:
                        snapshot = {
                            'total_stats': dict(total_stats),
                            'line_stats': {w: dict(l) for w, l in line_stats.items()}
                        }
                        tmp.write(json.dumps(snapshot) + '\n')
                        tmp.flush()

                        # Очищаем память, но оставляем основные данные
                        logger.info(f"Task {task_id}: flushed after {lines_processed} lines")

            # Агрегируем все снэпшоты
            final_total = defaultdict(int)
            final_line = defaultdict(lambda: defaultdict(int))

            with open(temp_path, 'r') as tmp:
                for line in tmp:
                    snapshot = json.loads(line)
                    for word, count in snapshot['total_stats'].items():
                        final_total[word] += count
                    for word, lines in snapshot['line_stats'].items():
                        for line_idx, cnt in lines.items():
                            final_line[word][int(line_idx)] += cnt

            results = []
            for word, total in sorted(final_total.items(), key=lambda x: x[1], reverse=True):
                if final_line[word]:
                    max_line = max(final_line[word].keys())
                    line_counts = [final_line[word].get(i, 0) for i in range(max_line + 1)]
                else:
                    line_counts = []

                results.append({
                    'word': word,
                    'total_count': total,
                    'line_counts': line_counts
                })

            return results

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # ========== СТРАТЕГИЯ 3: Streaming (для файлов 1GB - 5GB) ==========

    async def _process_streaming(self, file_path: str, normalizer, task_id: str) -> list[dict]:
        """
        Полностью потоковая обработка через SQLite.
        Память: ~50MB постоянно
        """
        db_path = os.path.join(self.temp_stats_dir, f"{task_id}.db")

        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute('''
                             CREATE TABLE word_stats
                             (
                                 word        TEXT PRIMARY KEY,
                                 total_count INTEGER DEFAULT 0
                             )
                             ''')
                conn.execute('''
                             CREATE TABLE line_stats
                             (
                                 word       TEXT,
                                 line_index INTEGER,
                                 count      INTEGER
                             )
                             ''')
                conn.execute('CREATE INDEX idx_word ON line_stats(word)')
                conn.commit()

            lines_processed = 0

            with open(file_path, 'r', encoding='utf-8') as f:
                for line_idx, line in enumerate(f):
                    line = line.strip()
                    if line:
                        words = normalizer.normalize(line)
                        word_counts = Counter(words)

                        with sqlite3.connect(db_path) as conn:
                            cursor = conn.cursor()

                            for word, count in word_counts.items():
                                # Обновляем общую статистику
                                cursor.execute('''
                                               INSERT INTO word_stats (word, total_count)
                                               VALUES (?, ?) ON CONFLICT(word) DO
                                               UPDATE SET
                                                   total_count = total_count + ?
                                               ''', (word, count, count))

                                # Добавляем построчную статистику
                                cursor.execute('''
                                               INSERT INTO line_stats (word, line_index, count)
                                               VALUES (?, ?, ?)
                                               ''', (word, line_idx, count))

                            conn.commit()

                    lines_processed += 1

                    if lines_processed % 100000 == 0:
                        logger.info(f"Task {task_id}: streaming {lines_processed} lines")

            results = []
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute('SELECT word, total_count FROM word_stats ORDER BY total_count DESC')
                word_totals = cursor.fetchall()

                for word, total in word_totals:
                    cursor = conn.execute('''
                                          SELECT line_index, SUM(count) as cnt
                                          FROM line_stats
                                          WHERE word = ?
                                          GROUP BY line_index
                                          ORDER BY line_index
                                          ''', (word,))
                    line_counts = [cnt for _, cnt in cursor]

                    results.append({
                        'word': word,
                        'total_count': total,
                        'line_counts': line_counts
                    })

            return results

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)