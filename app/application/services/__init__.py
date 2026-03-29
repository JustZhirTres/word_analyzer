"""Сервисы приложения"""
from .word_normalizer import WordNormalizerService, create_word_normalizer
from .excel_generator import ExcelGeneratorService

__all__ = [
    'WordNormalizerService',
    'create_word_normalizer',
    'ExcelGeneratorService',
]