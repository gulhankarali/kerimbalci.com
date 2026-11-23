"""dataset_builder modulunun cevrimdisi testleri (ag yok; sahte fetch)."""

import json

from kerimbalci_com.config import get_settings
from kerimbalci_com.dataset_builder.crawl import (
    crawl, discover_urls, extract_text, parse_sitemap, split_groups, stem_for_url,
)
from kerimbalci_com.dataset_builder.merge import merge, normalize

NS = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
INDEX = f'<sitemapindex {NS}><sitemap><loc>https://s.com/sitemap-posts.xml</loc></sitemap></sitemapindex>'
POSTS = (f'<urlset {NS}><url><loc>https://s.com/</loc></url>'
         '<url><loc>https://s.com/tag/ene/</loc></url>'
         '<url><loc>https://s.com/yazi-1/</loc></url>'
         '<url><loc>https://s.com/content/a.jpg</loc></url></urlset>')
HTML = """<html><head><meta property="og:title" content="Baslik">
<meta property="article:tag" content="ENE"><script>x()</script></head>
<body><nav>Menu</nav><h1>Baslik</h1><p>Birinci&nbsp;paragraf.</p><p>Ikinci</p>
<footer>Instagram</footer></body></html>"""
PAGES = {
    "https://s.com/sitemap.xml": INDEX,
    "https://s.com/sitemap-posts.xml": POSTS,
    "https://s.com/": HTML, "https://s.com/tag/ene/": HTML, "https://s.com/yazi-1/": HTML,
}


def test_stem_for_url():
    assert stem_for_url("https://s.com/") == "home"
    assert stem_for_url("https://s.com/tag/ene-makdisi/") == "tag_ene-makdisi"
    assert stem_for_url("https://s.com/bir-yazi/") == "bir-yazi"


def test_sitemap_ve_url_kesfi_gorselleri_atlar():
    assert parse_sitemap(INDEX) == ["https://s.com/sitemap-posts.xml"]
    assert discover_urls("https://s.com", PAGES.__getitem__) == [
        "https://s.com/", "https://s.com/tag/ene/", "https://s.com/yazi-1/"
    ]


def test_extract_text_meta_ve_govde():
    meta_line, body = extract_text(HTML).split("\n\n", 1)
    assert json.loads(meta_line) == {"og:title": ["Baslik"], "article:tag": ["ENE"]}
    assert "Birinci\xa0paragraf." in body and "Ikinci" in body
    assert "Menu" not in body and "Instagram" not in body and "x()" not in body


def test_crawl_dosyalari_ve_manifesti_yazar(monkeypatch, tmp_path):
    monkeypatch.setenv("SITE_URL", "https://s.com")
    monkeypatch.setenv("SITE_WORKDIR", str(tmp_path / "site"))
    pages = {**PAGES, "https://s.com/yazi-1/": None}

    def fetch(url):
        if pages[url] is None:
            raise OSError("404")
        return pages[url]

    manifest = crawl(get_settings(), fetch)
    assert manifest == {"home": "https://s.com/", "tag_ene": "https://s.com/tag/ene/"}
    assert (tmp_path / "site" / "text" / "home.txt").exists()
    assert json.loads((tmp_path / "site" / "manifest.json").read_text()) == manifest


def test_split_groups_dengeli(tmp_path):
    for name, words in {"a": 100, "b": 60, "c": 50, "d": 10}.items():
        (tmp_path / f"{name}.txt").write_text("k " * words)
    groups = split_groups(tmp_path, 2)
    assert sorted(map(sorted, groups)) == [["a.txt", "d.txt"], ["b.txt", "c.txt"]]  # 110 + 110


def _merge_fixture(tmp_path):
    work, gen, ds = tmp_path / "site", tmp_path / "gen", tmp_path / "ds"
    (work / "text").mkdir(parents=True)
    gen.mkdir()
    ds.mkdir()
    (work / "text" / "yazi.txt").write_text("{}\n\nKerim Balcı\xa0Bafra'da doğdu. Sonra okudu.", encoding="utf-8")
    (work / "manifest.json").write_text(json.dumps({"yazi": "https://s.com/yazi/"}))
    (ds / "unanswerable.json").write_text(json.dumps([
        {"id": "unans-009", "input": "Takim?", "expected_output": "Bilinmiyor.",
         "category": "unanswerable", "source_url": None},
        {"id": "unans-010", "input": "Eski", "expected_output": "x",
         "category": "unanswerable", "source_url": "https://s.com/eski/"},
    ]))
    decomposed = "Kerim Balcı Bafra'da doğdu.".replace("ğ", "ğ")  # NFD
    (gen / "A.json").write_text(json.dumps([
        {"input": "Nerede doğdu?", "expected_output": "Bafra'da.", "category": "direct_fact",
         "source_file": "yazi.txt", "evidence": decomposed},
        {"input": "Uydurma?", "expected_output": "x", "category": "direct_fact",
         "source_file": "yazi.txt", "evidence": "Bu cümle metinde yok."},
        {"input": "İzmir'de mi doğdu?", "expected_output": "Hayır, Bafra.", "category": "false_premise",
         "false_claim": "İzmir", "source_file": "yazi.txt", "evidence": "Bafra'da doğdu."},
    ], ensure_ascii=False), encoding="utf-8")
    return work, gen, ds


def test_merge_dogrular_normalize_eder_ve_elle_kayitlari_korur(tmp_path):
    work, gen, ds = _merge_fixture(tmp_path)
    report = merge(gen, work, ds)

    assert report.written == {"unanswerable": 1, "direct_fact": 1, "false_premise": 1}
    assert len(report.rejected) == 1 and "Uydurma" in report.rejected[0][1]
    fact = json.loads((ds / "direct_facts.json").read_text(encoding="utf-8"))[0]
    assert fact["id"] == "fact-001" and fact["source_url"] == "https://s.com/yazi/"
    assert fact["evidence"] == "Kerim Balcı Bafra'da doğdu."  # NFC'ye cevrildi
    premise = json.loads((ds / "false_premise.json").read_text(encoding="utf-8"))[0]
    assert premise["false_claim"] == "İzmir"
    unans = json.loads((ds / "unanswerable.json").read_text(encoding="utf-8"))
    assert unans == [{"id": "unans-001", "input": "Takim?", "expected_output": "Bilinmiyor.",
                      "category": "unanswerable", "source_url": None}]


def test_normalize():
    assert normalize(" a\xa0\n b ") == "a b"
