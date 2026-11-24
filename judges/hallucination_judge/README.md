# Hallucination Judge

deepeval `GEval` hakem yapılandırmaları. Factuality hakemiyle aynı şemayı
kullanır (bkz. `../factuality_judge/README.md`); hakem
`judge_config.load_judge(level, judges=HALLUCINATION_JUDGES)` ile kurulur.

| Seviye | Dosya | Ne kontrol eder? |
|---|---|---|
| 1 | `hallucination_judge_level1_basic.yaml` | Kanıtta ve beklenen cevapta dayanağı olmayan **bariz** bir uydurma var mı? |
| 2 | `hallucination_judge_level2_intermediate.yaml` | + iddia iddia denetim: temkinli tahminler, yanlış atıf, genel bilgiden ekleme |
| 3 | `hallucination_judge_level3_advanced.yaml` | + kategoriye özel tuzak kontrolü (`{hallucination_trap}`) |

Üç seviye de `context` (= kaydın `evidence` alıntısı) ve `expected_output`
kullanır; fark denetimin derinliğindedir. "Sitede bu bilgi yok" demek hiçbir
seviyede uydurma sayılmaz.

Seçim: `.env` → `HALLUCINATION_JUDGE_LEVEL=1|2|3` (varsayılan 3).
Eşik: YAML'daki `threshold`; `.env` → `EVAL_HALLUCINATION_THRESHOLD` doluysa onu ezer.
Ton/stil bu hakemde yok sayılır; onları `../expected_behavior_judge/` ölçer
(`EVAL_EXPECTED_BEHAVIOR`).

`category_steps` anahtarları yalnızca hallucination kategorileri olabilir:
`fabricated_detail`, `fake_attribution`, `entity_confusion`, `unsupported_addition`.

## Değiştirme
YAML'ı düzenleyin → `uv run pytest tests/unit/test_judges.py` (şema) →
`HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k <kategori>` ile küçük deneme.
