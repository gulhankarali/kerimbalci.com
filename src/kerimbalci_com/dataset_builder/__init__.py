"""Siteden eval dataset'i uretme araclari.

Akis (bkz. instructions/dataset.md):
    1. crawl  : sitemap -> tum sayfalar -> duz metin (+ manifest.json)
    2. split  : metinleri kelime sayisina gore dengeli gruplara boler
    3. (LLM)  : her grup icin instructions/dataset.md -> "Uretici Prompt"
    4. merge  : uretilen JSON'lari evidence dogrulamasiyla dataset'e yazar
"""
