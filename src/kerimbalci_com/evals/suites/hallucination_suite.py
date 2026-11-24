"""Hallucination suite: dataset/hallucination + judges/hallucination_judge (+ expected_behavior_judge).

Factuality asks "is the answer right?"; hallucination asks "did the answer
invent something that is NOT on the site?". Case tag = dataset category:
  fabricated_detail    — the topic is on the site, the requested detail is not
  fake_attribution     — a statement/idea is attributed to the wrong person or was never said
  entity_confusion     — two similar entities on the site are mixed up
  unsupported_addition — the answer is on the site; the risk is unsupported additions from general knowledge

The record's `evidence` quote becomes LLMTestCase.context, and
`hallucination_trap` fills the {hallucination_trap} placeholder in the judge
steps. The judge level is selected with HALLUCINATION_JUDGE_LEVEL; the second
metric (Expected Behavior) is toggled with EVAL_EXPECTED_BEHAVIOR (see suites/common.py).
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
    """Builds the hallucination suite. async_mode=False for the runner (thread pool)."""
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
