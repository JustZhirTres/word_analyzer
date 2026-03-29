import os
import pandas as pd

from ...config.settings import settings


class ExcelGeneratorService:
    """Сервис для генерации Excel файлов"""

    async def generate(self, results: list[dict], task_id: str, original_filename: str) -> str:
        """
        Генерация Excel файла с тремя колонками.

        results: [
            {'word': 'привет', 'total_count': 100, 'line_counts': [1,2,1,3,...]},
            ...
        ]
        """
        data = []
        for result in results:
            line_counts_str = ','.join(str(c) for c in result['line_counts'])
            data.append({
                'Словоформа': result['word'],
                'Кол-во во всём документе': result['total_count'],
                'Кол-во в каждой строке': line_counts_str
            })

        df = pd.DataFrame(data)

        result_filename = f"{task_id}_{original_filename}_analysis.xlsx"
        result_path = os.path.join(settings.RESULTS_DIR, result_filename)

        df.to_excel(
            result_path,
            index=False,
            sheet_name='Частотный анализ'
        )

        return result_path