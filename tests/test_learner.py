from maaya.learner import ItemState, LearnerState


def test_ladder_offsets():
    st = LearnerState()
    st.introduce(["a"], 1)
    assert st.items["a"].next_due == 2
    st.complete(2, [("a", 2)])
    assert st.items["a"].next_due == 3
    st.complete(3, [("a", 2)])
    assert st.items["a"].next_due == 6
    st.complete(6, [("a", 3)])
    assert st.items["a"].next_due == 11
    st.complete(11, [("a", 4)])
    assert st.items["a"].next_due == 21
    st.complete(21, [("a", 4)])
    assert st.items["a"].next_due == 46


def test_failure_resets_ladder():
    st = LearnerState()
    st.introduce(["a"], 1)
    st.complete(2, [("a", 2)])
    st.complete(3, [("a", 2)], failed={"a"})
    assert st.items["a"].rung == 0
    assert st.items["a"].next_due == 4


def test_due_ordering_and_stage():
    st = LearnerState()
    st.introduce(["a"], 1)
    st.introduce(["b"], 2)
    assert st.due(3) == [("a", 2), ("b", 2)]
    st.complete(3, [("a", 2), ("b", 2)])
    assert st.due(4) == [("a", 3), ("b", 3)]  # both: last 3, rung 1 -> gap 1
    st.complete(4, [("a", 3), ("b", 3)])
    assert st.due(5) == []  # last 4, rung 2 -> gap 3 -> due 7
    assert st.due(7) == [("a", 4), ("b", 4)]
    assert ItemState(introduced=1, last=1, rung=3).stage == 4


def test_roundtrip(tmp_path):
    st = LearnerState()
    st.introduce(["a"], 1)
    st.save(tmp_path / "l.json")
    assert LearnerState.load(tmp_path / "l.json").items["a"].introduced == 1
