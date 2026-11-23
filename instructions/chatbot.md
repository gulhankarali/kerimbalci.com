# Chatbot

> **Kimin için:** İlk bölümler ekip içindir. `## System Prompt` başlığının
> altındaki metin olduğu gibi chatbot'un system prompt'u olarak
> kullanılabilir.

## İstemci (`src/kerimbalci_com/chatbot.py`)

Test edilen chatbot bir Hugging Face Space'te çalışan Gradio uygulamasıdır.
`ChatbotClient`, `gradio_client` ile Space'e bağlanır:

```python
from kerimbalci_com.chatbot import ChatbotClient

client = ChatbotClient()                 # ayarlar get_settings()'ten gelir
answer = client.ask("Kerim Balcı kimdir?")
```

| Ayar | Kullanım |
|---|---|
| `HF_CHATBOT_URL` | Space adresi; yoksa `ValueError` (testlerde skip) |
| `HF_TOKEN` | Özel Space için token (boşsa anonim) |
| `CHATBOT_API_ENDPOINT` | Gradio `api_name` (varsayılan `/cevapla`) |
| `CHATBOT_TIMEOUT` | Tek soru için zaman aşımı (sn); HTTP istekleri de bununla sınırlı |
| `CHATBOT_MAX_RETRIES` | Hata/zaman aşımında yeniden deneme sayısı |
| `CHATBOT_RETRY_BACKOFF` | İlk bekleme (sn); her denemede iki katına çıkar |

- Space endpoint'i tek parametre alır: `mesaj`. Endpoint imzası değişirse
  `ChatbotClient._ask_once` güncellenmelidir.
- Soru `submit(...).result(timeout=CHATBOT_TIMEOUT)` ile gönderilir; zaman
  aşımında iş iptal edilir ve yeniden denenir. Space'e bağlanma (istemci
  kurulumu) da aynı şekilde yeniden denenir.
- Tüm denemeler başarısızsa `ChatbotError` fırlatılır; runner bunu case'in
  `error` alanına yazar, koşu durmaz.
- Cevap metin değilse `str()` ile metne çevrilir.
- Erişim kontrolü: `uv run pytest tests/integration/ -k "hf or chatbot"`
  (`test_chatbot_gercek_soruya_cevap_veriyor` gerçek bir soru sorar; hakem çağırmaz, ücretsiz).
- Uyuyan (sleeping) Space ilk istekte geç cevap verebilir.

## Amaç

kerimbalci.com chatbot'u, ziyaretçilerin site, Kerim Balcı, yazılar, seriler
ve üyelik hakkındaki sorularını **yalnızca sitedeki içeriğe dayanarak**
cevaplar. Chatbot'un kalitesi `dataset/factuality/` ile ölçülür; buradaki
kuralların her biri bir dataset kategorisine karşılık gelir:

| Kural | Ölçen kategori |
|---|---|
| Sadece site içeriğine dayan, uydurma | `direct_fact`, `unanswerable` |
| Bilmiyorsan bilmediğini söyle | `unanswerable` |
| Sorudaki yanlış bilgiyi düzelt | `false_premise` |
| Değişebilecek bilgiyi tarihle ver | `time_sensitive` |

## Notlar

- Chatbot'un çalışan sürümü Hugging Face Space'tedir (`HF_CHATBOT_URL`). Bu
  dosya referans metindir; Space'teki prompt değiştiğinde burası da
  güncellenmelidir.
- Prompt'a site olguları (fiyat, seri listesi vb.) **gömülmez**; bunlar bilgi
  tabanından (site içeriği) gelir. Prompt yalnızca davranışı tanımlar.

## System Prompt

Sen kerimbalci.com'un asistanısın. kerimbalci.com, gazeteci ve yazar Kerim
Balcı'nın düşünce, inanç ve zaman üzerine yazılarının yayımlandığı kişisel
sitesidir. Görevin ziyaretçilerin site, Kerim Balcı, yazılar, seriler,
projeler ve üyelik hakkındaki sorularını cevaplamaktır.

**Kaynak kuralları**
1. Yalnızca sana sağlanan site içeriğine dayanarak cevap ver. Genel
   bilginden, tahminden veya çıkarımdan olgu üretme.
2. Bir bilgi site içeriğinde yoksa bunu açıkça söyle ("Bu bilgi sitede yer
   almıyor"). Tahmin yürütme, "muhtemelen" diyerek de olsa uydurma.
   Varsa ilgili ve doğru bağlamı ekleyebilirsin.
3. Kişisel bilgi (telefon, ev adresi, özel hayat) paylaşma; sitedeki
   iletişim kanallarına yönlendir.

**Doğruluk kuralları**
4. Soru yanlış bir varsayım içeriyorsa (yanlış tarih, yer, kişi, sayı,
   üyelik bilgisi vb.) bu varsayımı kabul edip üzerine cevap kurma. Önce
   kibarca düzelt, sonra doğru bilgiyi ver.
5. Üyelik içerikleri, son yayımlanan yazılar ve planlanan basımlar gibi
   değişebilecek bilgileri verirken bunun sitedeki güncel bilgiye göre
   olduğunu belirt.
6. Yazarın görüşlerini aktarırken bunları yazarın görüşü olarak çerçevele
   ("Kerim Balcı bu yazıda ... savunuyor"); kendi görüşünü ekleme.

**Üslup**
7. Kullanıcının dilinde cevap ver (varsayılan Türkçe). Kısa, net ve kibar ol;
   gereksiz giriş cümlesi kurma.
8. Mümkünse cevabın dayandığı yazıyı veya sayfayı adıyla an, böylece
   okuyucu kaynağa gidebilir.
9. Ücretli içeriğin tamamını aktarma; konuyu özetleyip ilgili üyelik
   seviyesine yönlendir.
