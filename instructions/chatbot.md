# Chatbot

> **Audience:** the first sections are for the team. The text under the
> `## System Prompt` heading is a verbatim copy of the chatbot's system prompt
> and stays in Turkish on purpose (see the note there).

## Client (`src/kerimbalci_com/chatbot.py`)

The chatbot under test is a Gradio app running on a Hugging Face Space.
`ChatbotClient` connects to the Space with `gradio_client`:

```python
from kerimbalci_com.chatbot import ChatbotClient

client = ChatbotClient()                 # settings come from get_settings()
answer = client.ask("Kerim Balcı kimdir?")
```

| Setting | Usage |
|---|---|
| `HF_CHATBOT_URL` | Space URL; `ValueError` if missing (skip in tests) |
| `HF_TOKEN` | Token for a private Space (anonymous if empty) |
| `CHATBOT_API_ENDPOINT` | Gradio `api_name` (default `/cevapla`) |
| `CHATBOT_TIMEOUT` | Timeout per question (s); HTTP requests are limited by it too |
| `CHATBOT_MAX_RETRIES` | Retries on error/timeout |
| `CHATBOT_RETRY_BACKOFF` | Initial backoff (s); doubles on every attempt |

- The Space endpoint takes one parameter: `mesaj`. If the endpoint signature
  changes, `ChatbotClient._ask_once` must be updated.
- The question is sent with `submit(...).result(timeout=CHATBOT_TIMEOUT)`; on
  timeout the job is cancelled and retried. Connecting to the Space (client
  setup) is retried the same way.
- If every attempt fails, `ChatbotError` is raised; the runner stores it in the
  case's `error` field and the run continues.
- A non-text answer is converted to text with `str()`.
- Access check: `uv run pytest tests/integration/ -k "hf or chatbot"`
  (`test_chatbot_answers_a_real_question` asks a real question; it does not
  call the judge and is free).
- A sleeping Space may answer the first request slowly.

## Purpose

The kerimbalci.com chatbot answers visitors' questions about the site, Kerim
Balcı, the articles, series and membership **based only on the site content**.
Its quality is measured with `dataset/factuality/` and `dataset/hallucination/`;
each rule below maps to a dataset category:

| Rule | Measured by |
|---|---|
| Rely only on the site content, do not invent | `direct_fact`, `unanswerable`, `fabricated_detail`, `unsupported_addition` |
| Say so when you do not know | `unanswerable`, `fabricated_detail` |
| Correct false information in the question | `false_premise`, `fake_attribution` |
| Attribute statements and properties to the right person/thing | `fake_attribution`, `entity_confusion` |
| Give information that may change with a date | `time_sensitive` |

## Notes

- The live version of the chatbot is on the Hugging Face Space
  (`HF_CHATBOT_URL`). This file is the reference text; when the prompt on the
  Space changes, update it here too.
- The behavior rules (the "Kaynak", "Doğruluk", "Üslup" sections of the System
  Prompt below) are measured by the **Expected Behavior** judge:
  `judges/expected_behavior_judge/expected_behavior_judge.yaml`. If the rules
  change, update that YAML too.
- Site facts (prices, series list, etc.) are **not** embedded in the prompt;
  they come from the knowledge base (site content). The prompt only defines
  behavior.

## System Prompt

> Kept in Turkish: this is a verbatim copy of the prompt deployed on the Space.
> In short, it tells the assistant to answer only from the site content, to say
> clearly when something is not on the site, to correct false assumptions
> politely, to flag information that may change, to frame the author's views
> as his own, to answer in the user's language concisely, to name its source
> page, and not to reproduce paid content.

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
