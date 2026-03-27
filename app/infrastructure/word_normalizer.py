import pymorphy3
from app.domain.services import WordNormalizerService


def create_word_normalizer() -> WordNormalizerService:
    """Создаёт и возвращает сервис нормализации слов"""
    morph = pymorphy3.MorphAnalyzer()
    return WordNormalizerService(morph)