# Dataset Hazırlama Talimatları

> **Kimin için:** Üst kısım ekip içindir (süreç ve kalite kuralları).
> `## Üretici Prompt` başlığının altındaki metin, soru-cevap üretecek
> modele (Claude vb.) olduğu gibi verilir.

## Genel ilkeler

1. **Tek doğruluk kaynağı site içeriğidir.** Beklenen cevaplar yalnızca
   kerimbalci.com'daki public metne dayanır; modelin genel bilgisi veya bir
   özet aracının çıktısı kaynak sayılmaz.
2. **Her kayıt kanıtlıdır.** `evidence` alanı kaynak sayfadan birebir
   alıntıdır ve otomatik olarak sayfa metninde aranarak doğrulanır.
   Doğrulanamayan kayıt dataset'e girmez.
3. **Kaynak çeşitliliği.** Sorular sitenin tamamına yayılır; tek sayfadan
   en fazla 3 soru üretilir. Biyografi sayfası dataset'e hâkim olmamalıdır.
4. **Paywall.** Ücretli yazılarda yalnızca herkese açık kısım kullanılır.
5. Şema ve dosya düzeni için: `dataset/factuality/README.md`.

## Kategoriler ve hedef oranlar

| Kategori | Oran | Ne test eder? |
|---|---|---|
| `direct_fact` | ~%55 | Sitede açıkça yazan tek bir olgu |
| `false_premise` | ~%25 | Yanlış varsayımı düzeltme (`false_claim` zorunlu) |
| `time_sensitive` | ~%12 | Değişebilecek bilgi (`valid_as_of` zorunlu) |
| `unanswerable` | ~%8 | Sitede olmayan bilgide uydurmama |

## Süreç

Kod: `src/kerimbalci_com/dataset_builder/` (ayarlar: `SITE_URL`, `SITE_WORKDIR`).

1. **Tara ve metne çevir:**
   `uv run python -m kerimbalci_com.dataset_builder crawl`
   `SITE_URL/sitemap.xml` → alt sitemap'ler → tüm sayfalar. HTML'den
   script/style/nav/header/footer/form çıkarılır; her dosyanın ilk satırı
   meta (og:title, article:published_time, article:tag) JSON'dur. Çıktı:
   `SITE_WORKDIR/text/<stem>.txt` + `SITE_WORKDIR/manifest.json` (stem → URL).
2. **Grupla:** `uv run python -m kerimbalci_com.dataset_builder split --groups 4`
   Metinleri kelime sayısına göre dengeli gruplara böler. Gruplar paralel
   üretilebilir.
3. **Üret:** Her grup için aşağıdaki Üretici Prompt'u, grubun dosya listesi
   ve kategori hedefleriyle birlikte modele ver; çıktıları tek bir klasöre
   (ör. `.cache/generated/A.json`, `B.json` …) kaydet.
4. **Doğrula ve birleştir:**
   `uv run python -m kerimbalci_com.dataset_builder merge .cache/generated`
   Her `evidence`, Unicode NFC normalizasyonu ve boşluk sadeleştirmesinden
   sonra kaynak metinde aranır; bulunamayan kayıt reddedilir ve loglanır.
   Geçenlere `id` (`fact-001`, `premise-001`, `unans-001`, `time-001`) ve
   manifest'ten `source_url` atanır. Mevcut dataset'teki kaynaksız
   (`source_url: null`) elle yazılmış kayıtlar korunur. Son adımda şema
   `load_factuality()` ile doğrulanır.
5. **Elle düzeltme:** Gözden geçirmede düzeltilecek kayıtları `.cache/generated`
   içindeki kaynak JSON'da düzeltip `merge`'ü yeniden çalıştırın; böylece
   düzeltmeler bir sonraki üretimde kaybolmaz.
6. **Gözden geçir (insan):** Aşağıdaki kontrol listesini uygula.
7. **Test:** `uv run pytest tests/unit/test_datasets.py` (şema), ardından küçük
   bir eval denemesi: `uv run pytest -m eval tests/factuality/ -k <kategori>`.

### Bilinen tuzaklar

- Sayfalarda bölünmez boşluk (`\xa0`) ve ayrık yazılmış Türkçe harfler
  (NFD) bulunabilir; doğrulamada normalize edin.
- Footer metinden çıkarıldığı için sosyal medya linkleri gibi footer
  bilgileri metinde görünmez. "Sitede X yok" diyen `unanswerable`
  kayıtlarını canlı sitede ayrıca kontrol edin.
- E-posta adresleri Cloudflare tarafından gizlenir (`[email protected]`);
  kanıt olarak kullanmayın.
- Etiket sayfalarındaki "en son yazı" sırası varsayımdır (Ghost'ta yeniden
  eskiye); `time_sensitive` olarak işaretleyin.

### Gözden geçirme kontrol listesi

- [ ] Cevap, `evidence` alıntısının söylediğinden fazlasını iddia etmiyor.
- [ ] `false_premise` sorusundaki yanlış bilgi gerçekten yanlış ve makul
      (kullanıcının gerçekten yapabileceği bir hata).
- [ ] `unanswerable` sorusunun cevabı sitenin hiçbir yerinde yok (canlı
      sitede arandı).
- [ ] `time_sensitive` kayıtlarının `valid_as_of` tarihi güncel; eskiyenler
      yeniden doğrulandı.
- [ ] Yinelenen veya çok benzer soru yok.

## Üretici Prompt

Bir chatbot (kerimbalci.com hakkında soru cevaplayan) için factuality testi
hazırlıyoruz. Sana verilen metin dosyaları siteden indirilmiş sayfaların düz
metnidir. Her dosyanın ilk satırı JSON meta (og:title,
article:published_time, article:tag), sonrası sayfa metnidir. Ücretli
yazılarda metin paywall'da kesilmiş olabilir; SADECE metinde yazanı kullan.

**Kesin kurallar**
1. Beklenen cevaplar YALNIZCA dosyadaki metne dayanır. Genel bilginle
   ekleme yapma, çıkarım yapma.
2. Her kayıtta `evidence` alanı: kaynak metinden BİREBİR kopyalanmış
   (karakteri karakterine, aynı noktalama) 1-2 cümlelik alıntı. Bir script
   bu alıntının dosyada geçtiğini kontrol edecek; değiştirirsen kayıt
   atılır. Alıntıyı tek paragraftan al.
3. Sorular Türkçe, doğal, bir site ziyaretçisinin chatbot'a soracağı gibi.
   İngilizce yazılar için de soru Türkçe olabilir.
4. Sorular kısa ve tek bir doğrulanabilir olguya odaklı olsun; metinde
   açıkça söylenen iddia, olgu, isim, tarih veya sayıya dayan. Yazarın
   açıkça ifade ettiği görüş ("yazar X'i savunuyor") kabul edilir.
5. Dosyalara dengeli dağıt; tek bir dosyadan 3'ten fazla soru çıkarma.
6. Tekrarlı veya çok benzer soru yazma.
7. Bir bilginin sitede OLMADIĞINI iddia etmeden önce sana verilen tüm
   dosyalarda ara.

**Kategoriler**
- `direct_fact`: tek doğru cevabı olan olgu sorusu.
- `false_premise`: soru metindeki bir olguyu YANLIŞ varsayar;
  `expected_output` öncülün yanlış olduğunu söyler ve doğrusunu verir.
  `false_claim` alanı zorunlu (yanlış iddianın kısa hali). `evidence` doğru
  bilgiyi gösterir.
- `unanswerable`: (yalnızca istenmişse) sitede cevabı OLMAYAN ama ilgili
  görünen soru; `expected_output` bilginin sitede bulunmadığını söyler,
  uydurmaz. `evidence`: konuyla ilgili en yakın bağlam alıntısı.
- `time_sensitive`: değişebilecek bilgi (üyelik içerikleri, yayın tarihi,
  serideki son yazı, planlanan şeyler). `valid_as_of`: üretim günü
  (YYYY-AA-GG).

**Çıktı:** Yalnızca bir JSON listesi. Her kayıt:

```json
{
  "input": "...",
  "expected_output": "1-3 cümle, tam ve kendi başına anlaşılır",
  "category": "direct_fact | false_premise | unanswerable | time_sensitive",
  "source_file": "<dosya>.txt",
  "evidence": "<birebir alıntı>",
  "false_claim": "... (yalnızca false_premise)",
  "valid_as_of": "YYYY-AA-GG (yalnızca time_sensitive)"
}
```

`id` ve `source_url` ekleme; bunlar birleştirme adımında atanır.
