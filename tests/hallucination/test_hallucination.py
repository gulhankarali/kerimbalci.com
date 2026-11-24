"""Chatbot hallucination (uydurma) degerlendirmesi — deepeval + Confident AI.

Suite tanimi kerimbalci_com.evals.suites.hallucination_suite modulundedir; bu
dosya ayni suite'i pytest/deepeval uzerinden calistirir ve sonuclari Confident
AI'ya gonderir. Fixture'lar: tests/conftest.py.
Paralel, yerel raporlu alternatif:
    uv run python -m kerimbalci_com.evals hallucination

Sorular : dataset/hallucination/*.json
Hakem   : judges/hallucination_judge/ (HALLUCINATION_JUDGE_LEVEL = 1 | 2 | 3)
Esik    : YAML'daki threshold; .env -> EVAL_HALLUCINATION_THRESHOLD doluysa o.

DIKKAT: Hakem model icin Anthropic API'ye ucretli istek atar.

Calistirma:
    HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k fab-001   # tek kayit
    uv run pytest -m eval tests/hallucination/ -k fake_attribution                     # tek kategori
    uv run deepeval test run tests/hallucination/                                      # hepsi (50 soru)
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
    assert answer.strip(), "Chatbot bos cevap dondu"
    assert_test(suite.build_test_case(record, answer), suite.metrics_for(record))
