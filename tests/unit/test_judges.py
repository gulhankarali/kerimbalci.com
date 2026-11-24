"""Tests for the judge_config module and the judges/*/*.yaml judge files."""

import pytest
import yaml

from kerimbalci_com.datasets import ALL_CATEGORIES, CATEGORIES, HALLUCINATION_CATEGORIES
from kerimbalci_com.evals.judge_config import (
    EXPECTED_BEHAVIOR_JUDGE_FILE, HALLUCINATION_JUDGES, JudgeConfigError, load_judge, load_judge_file,
)

VALID = {
    "name": "Test",
    "level": 1,
    "description": "d",
    "threshold": 0.5,
    "evaluation_params": ["input", "actual_output", "expected_output", "context"],
    "criteria": "c",
    "evaluation_steps": ["step 1"],
    "rules": ["rule"],
    "category_steps": {"false_premise": ['False: "{false_claim}"']},
    "rubric": [
        {"score_range": [0, 4], "expected_outcome": "bad"},
        {"score_range": [5, 10], "expected_outcome": "good"},
    ],
}


def _write(tmp_path, data, name="factuality_judge_level1_test.yaml"):
    (tmp_path / name).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("level", [1, 2, 3])
def test_real_judge_files_are_valid(level):
    judge = load_judge(level)
    assert judge.level == level
    assert judge.source is not None and judge.source.name.startswith(f"factuality_judge_level{level}_")


def test_expected_behavior_judge_is_valid():
    judge = load_judge_file(EXPECTED_BEHAVIOR_JUDGE_FILE)
    assert judge.evaluation_params == ["input", "actual_output"]
    assert set(judge.category_steps) <= ALL_CATEGORIES
    assert any("Do NOT judge whether the facts" in s for s in judge.steps_for("direct_fact"))


@pytest.mark.parametrize("level", [1, 2, 3])
def test_real_hallucination_judges_are_valid(level):
    judge = load_judge(level, judges=HALLUCINATION_JUDGES)
    assert judge.level == level
    assert judge.source.name.startswith(f"hallucination_judge_level{level}_")
    assert "context" in judge.evaluation_params


def test_hallucination_level3_covers_all_categories():
    judge = load_judge(3, judges=HALLUCINATION_JUDGES)
    assert judge.category_steps.keys() == HALLUCINATION_CATEGORIES
    steps = judge.steps_for("fabricated_detail", hallucination_trap="TRAP")
    assert any("TRAP" in s for s in steps)


def test_hallucination_judge_rejects_factuality_category(tmp_path):
    data = {**VALID, "category_steps": {"false_premise": ["x"]}}
    _write(tmp_path, data, "hallucination_judge_level1_test.yaml")
    with pytest.raises(JudgeConfigError, match="unknown category"):
        load_judge(1, tmp_path, judges=HALLUCINATION_JUDGES)


def test_load_judge_file_missing_raises(tmp_path):
    with pytest.raises(JudgeConfigError, match="not found"):
        load_judge_file(tmp_path / "missing.yaml")


def test_level3_covers_all_categories():
    assert load_judge(3).category_steps.keys() == CATEGORIES


def test_steps_for_adds_rules_and_category(tmp_path):
    judge = load_judge(1, _write(tmp_path, VALID))
    assert judge.steps_for("false_premise", false_claim="X") == [
        "step 1", "Rule: rule", 'False: "X"'
    ]
    assert judge.steps_for("direct_fact") == ["step 1", "Rule: rule"]


def test_params_for_drops_context_without_evidence(tmp_path):
    judge = load_judge(1, _write(tmp_path, VALID))
    assert "context" in judge.params_for(has_context=True)
    assert "context" not in judge.params_for(has_context=False)


@pytest.mark.parametrize(
    "patch, message",
    [
        ({"criteria": ""}, "'criteria'"),
        ({"threshold": 1.5}, "threshold"),
        ({"evaluation_params": ["input", "foo"]}, "unknown evaluation_params"),
        ({"category_steps": {"other": ["x"]}}, "unknown category"),
        ({"rubric": [{"score_range": [0, 5], "expected_outcome": "a"},
                     {"score_range": [5, 10], "expected_outcome": "b"}]}, "overlaps"),
        ({"rubric": [{"score_range": [0, 4], "expected_outcome": "a"},
                     {"score_range": [6, 10], "expected_outcome": "b"}]}, "without gaps"),
        ({"rubric": [{"score_range": [0, 8], "expected_outcome": "a"}]}, "does not reach"),
        ({"rubric": [{"score_range": [0, 10]}]}, "invalid rubric item"),
        ({"level": 2}, "does not match"),
    ],
)
def test_invalid_yaml_is_rejected(tmp_path, patch, message):
    with pytest.raises(JudgeConfigError, match=message):
        load_judge(1, _write(tmp_path, {**VALID, **patch}))


def test_missing_or_extra_files(tmp_path):
    with pytest.raises(JudgeConfigError, match="found 0"):
        load_judge(1, tmp_path)
    _write(tmp_path, VALID, "factuality_judge_level1_a.yaml")
    _write(tmp_path, VALID, "factuality_judge_level1_b.yaml")
    with pytest.raises(JudgeConfigError, match="found 2"):
        load_judge(1, tmp_path)
