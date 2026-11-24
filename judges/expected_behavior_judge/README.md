# Expected Behavior Judge

A judge that scores the **behavior** of the answer: language, concision, focus,
framing of the author's views, tone, paid content. The rules are derived from
`instructions/chatbot.md` → System Prompt; if one changes, update the other.

- Factual correctness is **not** measured (that is the job of the Factuality /
  Hallucination metrics). Conversely, those YAMLs ignore tone/style; the
  metrics complement each other.
- `evaluation_params`: only `input` + `actual_output` (the expected answer is
  not a reference for behavior).
- Added as the second metric to every case in the factuality and hallucination
  suites; to turn it off set `.env` → `EVAL_EXPECTED_BEHAVIOR=false` (roughly
  halves the cost).
- The schema is the same as the factuality judge (see
  `judges/factuality_judge/README.md`); it is read with
  `src/kerimbalci_com/evals/judge_config.py` → `load_judge_file`.
