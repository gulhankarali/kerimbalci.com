"""judges modulunun ve judges/factuality_judge/*.yaml dosyalarinin testleri."""

import pytest
import yaml

from kerimbalci_com.datasets import CATEGORIES
from kerimbalci_com.evals.judge_config import (
    EXPECTED_BEHAVIOR_JUDGE_FILE, JudgeConfigError, load_judge, load_judge_file,
)

VALID = {
    "name": "Test",
    "level": 1,
    "description": "d",
    "threshold": 0.5,
    "evaluation_params": ["input", "actual_output", "expected_output", "context"],
    "criteria": "c",
    "evaluation_steps": ["adim 1"],
    "rules": ["kural"],
    "category_steps": {"false_premise": ['Yanlis: "{false_claim}"']},
    "rubric": [
        {"score_range": [0, 4], "expected_outcome": "kotu"},
        {"score_range": [5, 10], "expected_outcome": "iyi"},
    ],
}


def _write(tmp_path, data, name="factuality_judge_level1_test.yaml"):
    (tmp_path / name).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("level", [1, 2, 3])
def test_gercek_hakem_dosyalari_gecerli(level):
    judge = load_judge(level)
    assert judge.level == level
    assert judge.source is not None and judge.source.name.startswith(f"factuality_judge_level{level}_")


def test_expected_behavior_hakemi_gecerli():
    judge = load_judge_file(EXPECTED_BEHAVIOR_JUDGE_FILE)
    assert judge.evaluation_params == ["input", "actual_output"]
    assert set(judge.category_steps) <= CATEGORIES
    assert any("Do NOT judge whether the facts" in s for s in judge.steps_for("direct_fact"))


def test_load_judge_file_yoksa_hata(tmp_path):
    with pytest.raises(JudgeConfigError, match="bulunamadi"):
        load_judge_file(tmp_path / "yok.yaml")


def test_level3_tum_kategorileri_kapsar():
    assert load_judge(3).category_steps.keys() == CATEGORIES


def test_steps_for_kurallari_ve_kategoriyi_ekler(tmp_path):
    judge = load_judge(1, _write(tmp_path, VALID))
    assert judge.steps_for("false_premise", false_claim="X") == [
        "adim 1", "Rule: kural", 'Yanlis: "X"'
    ]
    assert judge.steps_for("direct_fact") == ["adim 1", "Rule: kural"]


def test_params_for_kanit_yoksa_context_cikar(tmp_path):
    judge = load_judge(1, _write(tmp_path, VALID))
    assert "context" in judge.params_for(has_context=True)
    assert "context" not in judge.params_for(has_context=False)


@pytest.mark.parametrize(
    "patch, message",
    [
        ({"criteria": ""}, "'criteria'"),
        ({"threshold": 1.5}, "threshold"),
        ({"evaluation_params": ["input", "foo"]}, "bilinmeyen evaluation_params"),
        ({"category_steps": {"baska": ["x"]}}, "bilinmeyen kategori"),
        ({"rubric": [{"score_range": [0, 5], "expected_outcome": "a"},
                     {"score_range": [5, 10], "expected_outcome": "b"}]}, "cakismasiz"),
        ({"rubric": [{"score_range": [0, 4], "expected_outcome": "a"},
                     {"score_range": [6, 10], "expected_outcome": "b"}]}, "bosluksuz"),
        ({"rubric": [{"score_range": [0, 8], "expected_outcome": "a"}]}, "ulasmiyor"),
        ({"rubric": [{"score_range": [0, 10]}]}, "rubric maddesi"),
        ({"level": 2}, "uyusmuyor"),
    ],
)
def test_hatali_yaml_yakalanir(tmp_path, patch, message):
    with pytest.raises(JudgeConfigError, match=message):
        load_judge(1, _write(tmp_path, {**VALID, **patch}))


def test_eksik_veya_fazla_dosya(tmp_path):
    with pytest.raises(JudgeConfigError, match="0 bulundu"):
        load_judge(1, tmp_path)
    _write(tmp_path, VALID, "factuality_judge_level1_a.yaml")
    _write(tmp_path, VALID, "factuality_judge_level1_b.yaml")
    with pytest.raises(JudgeConfigError, match="2 bulundu"):
        load_judge(1, tmp_path)
