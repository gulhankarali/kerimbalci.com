"""Hallucination suite: dataset/hallucination + judges/hallucination_judge (+ expected_behavior_judge).

Factuality "cevap dogru mu?" diye sorar; hallucination "cevapta sitede
OLMAYAN bir sey uyduruldu mu?" diye sorar. Case tag'i = dataset kategorisi:
  fabricated_detail    — konu sitede var, sorulan ayrinti yok
  fake_attribution     — soz/fikir yanlis kisiye atfediliyor veya hic soylenmemis
  entity_confusion     — sitede birbirine benzeyen iki varlik karistiriliyor
  unsupported_addition — cevap sitede var; risk, genel bilgiden kaynaksiz ekleme

Kaydin `evidence` alintisi LLMTestCase.context olur, `hallucination_trap`
hakem adimlarindaki {hallucination_trap} yer tutucusunu doldurur. Hakem
seviyesi HALLUCINATION_JUDGE_LEVEL ile secilir; ikinci metric (Expected
Behavior) EVAL_EXPECTED_BEHAVIOR ile acilip kapanir (bkz. suites/common.py).
"""

from deepeval.models import DeepEvalBaseLLM

from kerimbalci_com.config import Settings
from kerimbalci_com.datasets import load_hallucination
from kerimbalci_com.evals.eval_suite import EvalSuite
from kerimbalci_com.evals.judge_config import (
    EXPECTED_BEHAVIOR_JUDGE_FILE, HALLUCINATION_JUDGES, load_judge, load_judge_file,
)
from kerimbalci_com.evals.suites.common import build_test_case, judged_metrics

NAME = "hallucination"
PLACEHOLDER_FIELDS = ("hallucination_trap",)


def build_suite(settings: Settings, judge_model: DeepEvalBaseLLM, async_mode: bool = False) -> EvalSuite:
    """Hallucination suite'ini kurar. Runner (thread havuzu) icin async_mode=False."""
    config = load_judge(settings.hallucination_judge_level, judges=HALLUCINATION_JUDGES)
    behavior = load_judge_file(EXPECTED_BEHAVIOR_JUDGE_FILE) if settings.eval_expected_behavior else None

    return EvalSuite(
        name=f"{NAME}-L{config.level}",
        description=f"kerimbalci.com hallucination — {config.name}"
        + (f" + {behavior.name}" if behavior else ""),
        cases=tuple(load_hallucination()),
        metrics_for=judged_metrics(
            config,
            behavior,
            judge_model,
            threshold=settings.hallucination_threshold,
            placeholder_fields=PLACEHOLDER_FIELDS,
            async_mode=async_mode,
        ),
        build_test_case=build_test_case,
        tags_of=lambda case: [case["category"]],
    )
