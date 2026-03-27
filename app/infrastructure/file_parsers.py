import tempfile
import os
import docx
import PyPDF2
from typing import Optional


class FileParser:
    """Парсер различных форматов файлов"""

    @staticmethod
    def extract_text(file_path: str, extension: str) -> str:
        """
        Извлекает текст из файла.
        Для txt возвращает исходный путь.
        Для docx/pdf создаёт временный txt файл.
        """
        if extension == '.txt':
            return file_path

        temp_txt = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.txt',
            mode='w',
            encoding='utf-8',
            dir=tempfile.gettempdir()
        )

        try:
            if extension == '.docx':
                doc = docx.Document(file_path)
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        temp_txt.write(paragraph.text + '\n')

            elif extension == '.pdf':
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            temp_txt.write(text + '\n')

            temp_txt.close()
            return temp_txt.name

        except Exception as e:
            temp_txt.close()
            if os.path.exists(temp_txt.name):
                os.unlink(temp_txt.name)
            raise Exception(f"Failed to parse {extension}: {str(e)}")