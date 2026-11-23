"""Chatbot factuality (dogruluk) degerlendirmesi — deepeval + Confident AI.

Suite tanimi (case'ler, hakem, LLMTestCase) kerimbalci_com.evals.suites.factuality_suite
modulundedir; bu dosya ayni suite'i pytest/deepeval uzerinden calistirir ve
sonuclari Confident AI'ya gonderir. Fixture'lar: tests/conftest.py.
Paralel, yerel raporlu alternatif:
    uv run python -m kerimbalci_com.evals factuality

Sorular : dataset/factuality/*.json
Hakem   : judges/factuality_judge/ (FACTUALITY_JUDGE_LEVEL = 1 | 2 | 3)
Esik    : YAML'daki threshold; .env -> EVAL_FACTUALITY_THRESHOLD doluysa o.

DIKKAT: Hakem model icin Anthropic API'ye ucretli istek atar.

Calistirma:
    uv run deepeval test run tests/factuality/
    uv run pytest -m eval tests/factuality/ -k false_premise        # tek kategori
    FACTUALITY_JUDGE_LEVEL=1 uv run pytest -m eval tests/factuality/ -k fact-001
"""

import pytest
from deepeval import assert_test
from deepeval.models import AnthropicModel

from kerimbalci_com.chatbot import ChatbotClient
from kerimbalci_com.config import Settings
from kerimbalci_com.datasets import load_factuality
from kerimbalci_com.evals.eval_suite import EvalSuite
from kerimbalci_com.evals.suites import factuality_suite

pytestmark = [pytest.mark.integration, pytest.mark.eval]

RECORDS = load_factuality()


@pytest.fixture(scope="module")
def suite(settings: Settings, judge_model: AnthropicModel) -> EvalSuite:
    return factuality_suite.build_suite(settings, judge_model, async_mode=True)


@pytest.mark.parametrize("record", RECORDS, ids=[f"{r['category']}:{r['id']}" for r in RECORDS])
def test_factuality(chatbot: ChatbotClient, suite: EvalSuite, record: dict):
    answer = chatbot.ask(record["input"])
    assert answer.strip(), "Chatbot bos cevap dondu"
    assert_test(suite.build_test_case(record, answer), suite.metrics_for(record))
