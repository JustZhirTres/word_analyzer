"""Сервис нормализации слов"""
import pymorphy3
from typing import Generator
import re


class WordNormalizerService:
    """Сервис для нормализации слов (лемматизация)"""

    def __init__(self, morph: pymorphy3.MorphAnalyzer) -> None:
        self.morph = morph
        # Регулярка для поиска слов (только кириллица и латиница)
        self.word_pattern = re.compile(r'[а-яёa-z]+', re.IGNORECASE)

    def normalize(self, text: str) -> list[str]:
        """Нормализация текста: извлечение и лемматизация слов"""
        words = self._extract_words(text)
        lemmas = [self._lemmatize(word) for word in words]
        # Фильтруем пустые слова и короткие (менее 2 символов)
        return [lemma for lemma in lemmas if lemma and len(lemma) > 1]

    def _extract_words(self, text: str) -> Generator[str, None, None]:
        """Извлечение слов из текста"""
        for match in self.word_pattern.finditer(text.lower()):
            yield match.group()

    def _lemmatize(self, word: str) -> str:
        """Лемматизация одного слова"""
        try:
            parsed = self.morph.parse(word)[0]
            return parsed.normal_form
        except Exception:
            return word


def create_word_normalizer() -> WordNormalizerService:
    """Фабрика для создания сервиса нормализации"""
    morph = pymorphy3.MorphAnalyzer()
    return WordNormalizerService(morph)