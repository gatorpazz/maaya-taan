from maaya.curriculum import Dialogue, Item, Lesson, Line
from maaya.learner import LearnerState
from maaya.planner import plan_lesson


def mk_lesson(n: int, k: int = 8) -> Lesson:
    items = [Item(id=f"i{n}_{j}", yua=f"maya phrase {j}", en=f"english {j}", syllables=["phrase", f"maya phrase {j}"], cues=["cue one"],
                  transforms=[{"prompt_en": "transform", "yua": "maya x"}]) for j in range(k)]
    d = Dialogue(id=f"d{n}", setting_en="Two people talk.", lines=[Line(speaker="A", yua="maya phrase 0", en="english 0"), Line(speaker="B", yua="maya phrase 1", en="english 1")])
    return Lesson(number=n, title=f"Lesson {n}", opening=d, items=items, grammar_note="A note.")


def test_lesson_duration_and_structure():
    les = mk_lesson(1)
    plan = plan_lesson(les, {}, LearnerState())
    assert 1560 < plan.estimated_seconds < 1950
    kinds = [s.kind for s in plan.script.segments]
    assert kinds[0] == "narrator" and plan.script.segments[-1].kind == "narrator"
    notes = [s.note for s in plan.script.segments]
    for it in les.items:  # every new item: intro, buildup, within-lesson recalls
        assert f"{it.id}:intro" in notes
        assert sum(1 for n in notes if n in (f"{it.id}:s2", f"{it.id}:s3")) >= 3
    assert "grammar" in notes
    assert plan.reviewed == []


def test_cross_lesson_reviews_are_included_and_escalate():
    l1, l2 = mk_lesson(1), mk_lesson(2)
    st = LearnerState()
    st.introduce([i.id for i in l1.items], 1)
    st.complete(1, [])
    prior = {i.id: i for i in l1.items}
    plan = plan_lesson(l2, prior, st)
    assert {iid for iid, _ in plan.reviewed} == set(prior)
    assert all(stage == 2 for _, stage in plan.reviewed)
    st.introduce([i.id for i in l2.items], 2)
    st.complete(2, plan.reviewed)
    l3 = mk_lesson(3)
    plan3 = plan_lesson(l3, prior | {i.id: i for i in l2.items}, st)
    stages = dict(plan3.reviewed)
    assert stages[l1.items[0].id] == 3  # second review of lesson-1 items uses situational cue
    assert stages[l2.items[0].id] == 2


def test_recall_prompt_precedes_answer():
    plan = plan_lesson(mk_lesson(1), {}, LearnerState())
    segs = plan.script.segments
    for i, s in enumerate(segs):
        if s.note.endswith(":s2"):
            assert segs[i + 1].kind == "pause" and segs[i + 1].seconds >= 2.0
            assert segs[i + 2].kind == "maya"
