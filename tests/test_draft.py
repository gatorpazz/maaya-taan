from pathlib import Path

import yaml

from maaya.curriculum import Lesson, load_lesson
from maaya.draft import _fill_attestation, build_prompt, to_yaml


def test_prompt_has_corpus_and_taught():
    l1 = load_lesson(Path("curriculum/level1/lesson01.yaml"))
    prompt = build_prompt(2, l1.items)
    assert "bix_a_beel" in prompt and "Diiyáas" in prompt and "YUAES" in prompt


def test_yaml_roundtrip_and_attestation():
    l1 = load_lesson(Path("curriculum/level1/lesson01.yaml"))
    for it in l1.items:
        it.attested_by = []
    _fill_attestation(l1)
    assert all(it.attested_by for it in l1.items)
    again = Lesson.model_validate(yaml.safe_load(to_yaml(l1)))
    assert [i.id for i in again.items] == [i.id for i in l1.items]
