"""Turn a Lesson + learner state into a timed Script.

Lesson shape (Pimsleur):
  intro → opening dialogue (normal, then slow with meaning) → body → fillers → closing dialogue → outro
Body = new-item introductions (backward buildup + anticipation) interleaved with
within-lesson recalls of those items (+30 s, +2, +5, +10, +17 min) and cross-lesson
reviews of earlier items at escalating stages. Fillers (dialogue reconstruction,
situational cues, transforms, repeat rounds) run in priority order until the
lesson reaches its target length. Timing uses maaya.timing (calibrated on real
renders) so the planner can size a lesson without synthesizing audio.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from maaya import timing
from maaya.curriculum import Dialogue, Item, Lesson
from maaya.learner import LearnerState
from maaya.script import Script
from maaya.strings import LEVEL_NAME, NARRATOR

GAP = timing.GAP
WITHIN_LESSON = [30.0, 120.0, 300.0, 700.0]
SLOW = 0.7


@dataclass
class Plan:
    script: Script
    new_items: list[str]
    reviewed: list[tuple[str, int]]  # (item id, stage) for learner.complete
    estimated_seconds: float
    dropped_reviews: list[str] = field(default_factory=list)


class _Timeline:
    """Script builder that keeps a running duration estimate."""

    def __init__(self, script: Script, lang: str = "en"):
        self.s = script
        self.t = 0.0
        self.lang = lang
        self.S = NARRATOR[lang]

    def narrator(self, text: str, note: str = "") -> None:
        self.s.narrator(text, note)
        self.t += timing.narrator_seconds(text, self.lang) + GAP

    def maya(self, text: str, rate: float = 1.0, note: str = "", slice_of: str = "") -> None:
        self.s.maya(text, rate, note, slice_of=slice_of)
        self.t += timing.maya_seconds(text, rate) + GAP

    def pause(self, seconds: float, note: str = "") -> None:
        self.s.pause(seconds, note)
        self.t += seconds

    def response(self, text: str, rate: float = 1.0) -> None:
        """Anticipation gap before the answer."""
        self.s.response_pause(text, rate)
        self.t += self.s.segments[-1].seconds

    def repeat(self, text: str, rate: float = 1.0) -> None:
        """Gap to repeat what was just heard."""
        self.s.repeat_pause(text, rate)
        self.t += self.s.segments[-1].seconds


# ---------------------------------------------------------------- blocks


def _dialogue(tl: _Timeline, d: Dialogue, rate: float = 1.0, translate: bool = False) -> None:
    """Play a dialogue. With translate=True the narrator gives each line's meaning first."""
    for line in d.lines:
        if translate:
            tl.narrator(line.meaning(tl.lang), note=f"{d.id}:{line.speaker}:meaning")
        tl.maya(line.yua, rate, note=f"{d.id}:{line.speaker}")
        tl.pause(0.6 if rate == 1.0 else 1.0)


def _answer(tl: _Timeline, yua: str, note: str) -> None:
    """Pimsleur gives the answer, leaves room to repeat it, then gives it again."""
    tl.maya(yua, note=note)
    tl.repeat(yua)
    tl.maya(yua, note=note)
    tl.pause(timing.AFTER_ANSWER)


def _introduce(tl: _Timeline, it: Item, ordinal: int) -> None:
    """English meaning first, then the Maya; then sound-by-sound backward buildup
    (fragments are cut from the full-phrase audio at render time), then the
    first anticipation prompt."""
    S, lang = tl.S, tl.lang
    meaning = it.meaning(lang).rstrip(".")
    tl.narrator((S["next_item"] if ordinal else S["first_item"]).format(meaning=meaning), note=f"{it.id}:intro")
    tl.maya(it.yua, note=it.id)
    tl.pause(1.2)
    if it.literal_in(lang):
        tl.narrator(S["word_for_word"].format(literal=it.literal_in(lang)))
    if it.note_in(lang):
        tl.narrator(it.note_in(lang))
    chunks = it.syllables or [it.yua]
    tl.narrator(S["build_up"] if len(chunks) > 1 else S["listen_repeat"])
    glosses = it.glosses_in(lang)
    for i, c in enumerate(chunks):
        last = i == len(chunks) - 1
        rate = 1.0 if last else SLOW
        slice_of = "" if c.lower() == it.yua.lower() else it.yua
        if gloss := glosses.get(c):  # narrator never says Maya: meaning first, then the voice
            tl.narrator(f"{gloss[0].upper() + gloss[1:]}.", note=f"{it.id}:gloss")
        tl.maya(c, rate, note=f"{it.id}:build{i}", slice_of=slice_of)
        tl.repeat(c, rate)
        tl.maya(c, rate, note=f"{it.id}:build{i}", slice_of=slice_of)
        tl.repeat(c, rate)
    tl.narrator(S["say"].format(meaning=meaning), note=f"{it.id}:s2")
    tl.response(it.yua)
    _answer(tl, it.yua, f"{it.id}:answer")


def _recall(tl: _Timeline, it: Item, stage: int, k: int) -> None:
    """stage 2: how do you say; 3: situational cue; 4: transform (falls back to 3/2)."""
    S, lang = tl.S, tl.lang
    meaning = it.meaning(lang).rstrip(".")
    cues = it.cues_in(lang)
    if stage >= 4 and it.transforms:
        tr = it.transforms[k % len(it.transforms)]
        tl.narrator(S["how_do_you_say"].format(meaning=meaning), note=f"{it.id}:s4a")
        tl.response(it.yua)
        tl.maya(it.yua, note=it.id)
        tl.pause(0.6)
        tl.narrator(tr.prompt(lang), note=f"{it.id}:s4b")
        tl.response(tr.yua)
        _answer(tl, tr.yua, f"{it.id}:transform")
        return
    if stage >= 3 and cues:
        tl.narrator(cues[k % len(cues)], note=f"{it.id}:s3")
    else:
        prompt = S["how_do_you_say"].format(meaning=meaning) if k % 2 == 0 else S["say"].format(meaning=meaning)
        tl.narrator(prompt, note=f"{it.id}:s2")
    tl.response(it.yua)
    _answer(tl, it.yua, it.id)


def _reconstruct(tl: _Timeline, d: Dialogue) -> None:
    """Learner produces each line of the dialogue from its English."""
    tl.narrator(tl.S["reconstruct"].format(setting=d.setting(tl.lang)), note=f"{d.id}:reconstruct")
    for line in d.lines:
        tl.narrator(line.meaning(tl.lang), note=f"{d.id}:{line.speaker}:cue")
        tl.response(line.yua)
        tl.maya(line.yua, note=f"{d.id}:{line.speaker}")
        tl.pause(0.8)


def _dialogue_repeat(tl: _Timeline, d: Dialogue) -> None:
    """Listen and repeat each dialogue line, slowly then at speed."""
    tl.narrator(tl.S["repeat_lines"], note=f"{d.id}:repeat")
    for line in d.lines:
        tl.maya(line.yua, SLOW, note=f"{d.id}:{line.speaker}:slow")
        tl.repeat(line.yua, SLOW)
        tl.maya(line.yua, note=f"{d.id}:{line.speaker}")
        tl.repeat(line.yua)


def _repeat_round(tl: _Timeline, items: list[Item]) -> None:
    tl.narrator(tl.S["repeat_round"])
    for it in items:
        tl.maya(it.yua, SLOW, note=f"{it.id}:slow")
        tl.repeat(it.yua, SLOW)
        tl.maya(it.yua, note=f"{it.id}:fast")
        tl.repeat(it.yua)


# ---------------------------------------------------------------- planner


def plan_lesson(lesson: Lesson, prior: dict[str, Item], state: LearnerState, *, lang: str = "en", target_seconds: float = 1800.0) -> Plan:
    level_name = LEVEL_NAME[lang]
    lesson_word = {"en": "Lesson", "es": "Lección"}[lang]
    script = Script(lesson_id=f"L1-{lesson.number:02d}", title=f"Maaya T'aan {level_name} – {lesson_word} {lesson.number}: {lesson.title_in(lang)}")
    tl = _Timeline(script, lang)
    S = tl.S

    # intro + opening --------------------------------------------------
    tl.narrator(S["intro"].format(level=level_name, n=lesson.number))
    if lesson.number == 1:
        tl.narrator(S["l1_welcome"])
    tl.narrator(lesson.opening.setting(lang))
    _dialogue(tl, lesson.opening)
    tl.pause(1.0)
    tl.narrator(S["l1_method"] if lesson.number == 1 else S["once_more"])
    _dialogue(tl, lesson.opening)
    tl.pause(1.0)
    tl.narrator(S["with_meaning"])
    _dialogue(tl, lesson.opening, rate=SLOW, translate=True)
    tl.pause(1.0)
    tl.narrator(S["by_end"])

    # body: event-driven interleave -----------------------------------
    reviews = [(iid, st) for iid, st in state.due(lesson.number) if iid in prior]
    reviewed: list[tuple[str, int]] = []
    heap: list[tuple[float, int, str, int, int]] = []  # (due_t, seq, item_id, stage, k)
    seq = 0
    new_queue = list(lesson.items)
    items_by_id = {**prior, **{i.id: i for i in lesson.items}}
    recall_counts: dict[str, int] = {}
    grammar_said = False

    def push(iid: str, stage: int, delay: float, k: int) -> None:
        nonlocal seq
        heapq.heappush(heap, (tl.t + delay, seq, iid, stage, k))
        seq += 1

    # filler blocks, in Pimsleur priority order; consumed to fill gaps between
    # scheduled recalls, then to reach the target length. Items taught in this
    # lesson only get filler recalls once all of them have been introduced.
    closing = lesson.closing or lesson.opening
    closing_cost = sum(timing.maya_seconds(l.yua) + GAP + 0.6 for l in closing.lines) + 12
    taught = lambda: [it for it in lesson.items if it not in new_queue]
    fillers = [
        lambda: _reconstruct(tl, lesson.opening),
        lambda: [_recall(tl, it, 3, 1) for it in taught()],
        lambda: [_recall(tl, it, 4, 0) for it in taught() if it.transforms],
        lambda: _dialogue_repeat(tl, lesson.opening),
        lambda: _repeat_round(tl, taught()),
        lambda: [_recall(tl, it, 3, 2) for it in taught()],
        lambda: _reconstruct(tl, closing) if closing is not lesson.opening else None,
        lambda: [_recall(tl, it, 2, 3) for it in reversed(taught())],
        lambda: [_recall(tl, it, 4, 1) for it in taught() if it.transforms],
        lambda: [_recall(tl, it, 3, 3) for it in reversed(taught())],
    ]

    while new_queue or heap or reviews:
        if heap and heap[0][0] <= tl.t:
            _, _, iid, stage, k = heapq.heappop(heap)
            _recall(tl, items_by_id[iid], stage, k)
            if k + 1 < len(WITHIN_LESSON):
                push(iid, min(3, stage + 1), WITHIN_LESSON[k + 1] - WITHIN_LESSON[k], k + 1)
            continue
        if new_queue:
            it = new_queue.pop(0)
            _introduce(tl, it, len(lesson.items) - len(new_queue) - 1)
            push(it.id, 2, WITHIN_LESSON[0], 0)
            if not grammar_said and lesson.grammar_note_in(lang) and len(new_queue) == len(lesson.items) // 2:
                tl.narrator(lesson.grammar_note_in(lang), note="grammar")
                grammar_said = True
            continue
        if reviews:
            iid, stage = reviews.pop(0)
            k = recall_counts.get(iid, 0)
            _recall(tl, items_by_id[iid], stage, k)
            recall_counts[iid] = k + 1
            reviewed.append((iid, stage))
            continue
        if fillers:  # nothing due yet: fill the gap with real content, never with virtual time
            fillers.pop(0)()
            continue
        # out of fillers: take the next recall early
        _, _, iid, stage, k = heapq.heappop(heap)
        _recall(tl, items_by_id[iid], stage, k)
        if k + 1 < len(WITHIN_LESSON):
            push(iid, min(3, stage + 1), WITHIN_LESSON[k + 1] - WITHIN_LESSON[k], k + 1)

    if lesson.grammar_note_in(lang) and not grammar_said:
        tl.narrator(lesson.grammar_note_in(lang), note="grammar")

    # remaining fillers until the lesson is long enough --------------------
    while fillers and tl.t + closing_cost < target_seconds - 60:
        fillers.pop(0)()
    # still short (early lessons have few reviews): extra situational rounds
    k = 4
    while tl.t + closing_cost < target_seconds - 60 and k < 8:
        for it in lesson.items:
            if tl.t + closing_cost >= target_seconds - 30:
                break
            _recall(tl, it, 3, k)
        k += 1


    # closing ----------------------------------------------------------
    tl.narrator(S["closing"].format(setting=closing.setting(lang)))
    _dialogue(tl, closing)
    tl.narrator(S["end"].format(n=lesson.number))

    return Plan(script=script, new_items=[i.id for i in lesson.items], reviewed=reviewed, estimated_seconds=tl.t)
