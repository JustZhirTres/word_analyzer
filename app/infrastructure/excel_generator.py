from io import BytesIO
from openpyxl import Workbook
from app.domain.entities import WordFrequencyStats


class ExcelGenerator:
    """Генератор Excel файлов"""

    @staticmethod
    def generate(stats: WordFrequencyStats) -> BytesIO:
        """Создаёт Excel файл со статистикой"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Frequency"
        ws.append(["Словоформа", "Общее количество", "Количество по строкам"])

        # Сортируем по убыванию частоты
        sorted_items = sorted(
            stats.stats.items(),
            key=lambda x: x[1].total,
            reverse=True
        )

        for word_form, word_stat in sorted_items:
            per_line_str = ','.join(str(cnt) for cnt in word_stat.per_line)
            ws.append([word_form, word_stat.total, per_line_str])

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output