import re
from typing import Dict, Optional


class WordNormalizerService:
    """Сервис нормализации слов"""

    def __init__(self, morph):
        self.morph = morph

    def normalize(self, word: str) -> Optional[str]:
        """Приводит слово к нормальной форме"""
        # Очищаем от пунктуации (поддержка кириллицы)
        word_clean = re.sub(r'[^\w\'\u0400-\u04FF]+', '', word.lower())
        if not word_clean or len(word_clean) < 2:
            return None

        try:
            parsed = self.morph.parse(word_clean)[0]
            return parsed.normal_form
        except:
            return word_clean