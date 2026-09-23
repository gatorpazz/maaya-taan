"""Learner state: what was introduced when, how each review went, what's due.

Cross-lesson graduated interval recall, in *lessons* rather than days (you do
roughly one lesson per day). Each successful review lengthens the gap to the
next one: 1, 1, 3, 5, 10 lessons, then 25 (i.e. reviews at +1, +2, +5, +10,
+20 after introduction when done on time). Gaps count from the last review, so
a late review doesn't make the item immediately overdue again. A failure
restarts the ladder from the current lesson.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

GAPS = [1, 1, 3, 5, 10]
STEADY = 25


class Review(BaseModel):
    lesson: int
    stage: int
    ok: bool = True


class ItemState(BaseModel):
    introduced: int
    last: int  # lesson of the last touch (introduction or review); ladder counts from here
    rung: int = 0  # successful reviews on the current ladder
    reviews: list[Review] = Field(default_factory=list)

    @property
    def next_due(self) -> int:
        return self.last + (GAPS[self.rung] if self.rung < len(GAPS) else STEADY)

    @property
    def stage(self) -> int:
        """Recall difficulty for the next review: 2 = 'how do you say', 3 = situational cue, 4 = transform."""
        return min(4, 2 + self.rung)


class LearnerState(BaseModel):
    completed: list[int] = Field(default_factory=list)
    items: dict[str, ItemState] = Field(default_factory=dict)

    # persistence -------------------------------------------------------
    @classmethod
    def load(cls, path: Path) -> "LearnerState":
        return cls.model_validate_json(path.read_text()) if path.exists() else cls()

    def save(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2))

    # scheduling --------------------------------------------------------
    def due(self, lesson: int) -> list[tuple[str, int]]:
        """Item ids due for review in `lesson`, most overdue first, with their stage."""
        d = [(iid, st) for iid, st in self.items.items() if st.introduced < lesson and st.next_due <= lesson]
        d.sort(key=lambda p: (p[1].next_due, p[1].introduced, p[0]))
        return [(iid, st.stage) for iid, st in d]

    def introduce(self, item_ids: list[str], lesson: int) -> None:
        for iid in item_ids:
            self.items.setdefault(iid, ItemState(introduced=lesson, last=lesson))

    def complete(self, lesson: int, reviewed: list[tuple[str, int]], failed: set[str] = frozenset()) -> None:
        """Record a finished lesson. Reviews succeed unless the id is in `failed`."""
        for iid, stage in reviewed:
            st = self.items[iid]
            ok = iid not in failed
            st.reviews.append(Review(lesson=lesson, stage=stage, ok=ok))
            st.last = lesson
            st.rung = st.rung + 1 if ok else 0
        for iid in failed:  # a new item failed in its own lesson: keep rung 0, review next lesson
            if iid in self.items and self.items[iid].introduced == lesson:
                self.items[iid].last, self.items[iid].rung = lesson, 0
        if lesson not in self.completed:
            self.completed.append(lesson)
