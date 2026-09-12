"""Kurulum sırasında Türkçe/İngilizce EasyOCR modellerini önbelleğe alır."""

from belgeiz.extractors import EasyOCREngine


if __name__ == "__main__":
    EasyOCREngine()._get_reader()
    print("Türkçe/İngilizce OCR modelleri hazır.")

