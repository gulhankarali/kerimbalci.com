"""Chatbot hallucination evaluation — deepeval + Confident AI.

The suite definition lives in kerimbalci_com.evals.suites.hallucination_suite;
this file runs the same suite through pytest/deepeval and sends the results to
Confident AI. Fixtures: tests/conftest.py. Parallel alternative with local reports:
    uv run python -m kerimbalci_com.evals hallucination

Questions : dataset/hallucination/*.json
Judge     : judges/hallucination_judge/ (HALLUCINATION_JUDGE_LEVEL = 1 | 2 | 3)
Threshold : threshold from the YAML; .env -> EVAL_HALLUCINATION_THRESHOLD if set.

WARNING: makes paid requests to the Anthropic API for the judge model.

Usage:
    HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k fab-001   # one record
    uv run pytest -m eval tests/hallucination/ -k fake_attribution                     # one category
    uv run deepeval test run tests/hallucination/                                      # all (50 questions)
"""

import pytest
from deepeval import assert_test
from deepeval.models import AnthropicModel

from kerimbalci_com.chatbot import ChatbotClient
from kerimbalci_com.config import Settings
from kerimbalci_com.datasets import load_hallucination
from kerimbalci_com.evals.eval_suite import EvalSuite
from kerimbalci_com.evals.suites import hallucination_suite

pytestmark = [pytest.mark.integration, pytest.mark.eval]

RECORDS = load_hallucination()


@pytest.fixture(scope="module")
def suite(settings: Settings, judge_model: AnthropicModel) -> EvalSuite:
    return hallucination_suite.build_suite(settings, judge_model, async_mode=True)


@pytest.mark.parametrize("record", RECORDS, ids=[f"{r['category']}:{r['id']}" for r in RECORDS])
def test_hallucination(chatbot: ChatbotClient, suite: EvalSuite, record: dict):
    answer = chatbot.ask(record["input"])
    assert answer.strip(), "Chatbot returned an empty answer"
    assert_test(suite.build_test_case(record, answer), suite.metrics_for(record))
