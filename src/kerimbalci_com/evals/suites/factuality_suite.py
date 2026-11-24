"""Factuality suite: dataset/factuality + judges/factuality_judge (+ expected_behavior_judge).

Case tag'i = dataset kategorisi (direct_fact, false_premise, unanswerable,
time_sensitive). Kaydin `evidence` alintisi LLMTestCase.context olur;
hakem seviyesi FACTUALITY_JUDGE_LEVEL ile secilir.

Her case iki metric'le olculur (bkz. suites/common.py):
  1. Factuality        — olgular dogru mu? (judges/factuality_judge/level<N>)
  2. Expected Behavior — dil, kisalik, ton, cerceveleme (judges/expected_behavior_judge/)
     EVAL_EXPECTED_BEHAVIOR=false ile kapatilir.
"""

from deepeval.models import DeepEvalBaseLLM

from kerimbalci_com.config import Settings
from kerimbalci_com.datasets import load_factuality
from kerimbalci_com.evals.eval_suite import EvalSuite
from kerimbalci_com.evals.judge_config import (
    EXPECTED_BEHAVIOR_JUDGE_FILE, FACTUALITY_JUDGES, load_judge, load_judge_file,
)
from kerimbalci_com.evals.suites.common import build_test_case, judged_metrics

NAME = "factuality"
PLACEHOLDER_FIELDS = ("false_claim", "valid_as_of")


def build_suite(settings: Settings, judge_model: DeepEvalBaseLLM, async_mode: bool = False) -> EvalSuite:
    """Factuality suite'ini kurar. Runner (thread havuzu) icin async_mode=False."""
    config = load_judge(settings.factuality_judge_level, judges=FACTUALITY_JUDGES)
    behavior = load_judge_file(EXPECTED_BEHAVIOR_JUDGE_FILE) if settings.eval_expected_behavior else None

    return EvalSuite(
        name=f"{NAME}-L{config.level}",
        description=f"kerimbalci.com factuality — {config.name}"
        + (f" + {behavior.name}" if behavior else ""),
        cases=tuple(load_factuality()),
        metrics_for=judged_metrics(
            config,
            behavior,
            judge_model,
            threshold=settings.factuality_threshold,
            placeholder_fields=PLACEHOLDER_FIELDS,
            async_mode=async_mode,
        ),
        build_test_case=build_test_case,
        tags_of=lambda case: [case["category"]],
    )
