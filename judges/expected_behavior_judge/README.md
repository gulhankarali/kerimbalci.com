# Expected Behavior Judge

Cevabın **davranışını** puanlayan hakem: dil, kısalık, odak, yazarın
görüşünü çerçeveleme, ton, ücretli içerik. Kurallar
`instructions/chatbot.md` → System Prompt'tan türetilmiştir; biri
değişirse diğeri de güncellenmelidir.

- Olgusal doğruluk **ölçülmez** (Factuality metric'inin işi). Factuality
  YAML'ları da tersine tonu/stili yok sayar; iki metric birbirini tamamlar.
- `evaluation_params`: yalnızca `input` + `actual_output` (beklenen cevap
  davranış için referans değildir).
- Factuality ve hallucination suite'lerinde her case'e ikinci metric olarak eklenir; kapatmak
  için `.env` → `EVAL_EXPECTED_BEHAVIOR=false` (maliyeti yaklaşık yarıya indirir).
- Şema factuality hakemiyle aynıdır (bkz. `judges/factuality_judge/README.md`);
  `src/kerimbalci_com/evals/judge_config.py` → `load_judge_file` ile okunur.
