"""Attestation levels, including the hand-curated standard-phrase list (no audio, no corpus needed)."""
from maaya.attest import Attester, StandardPhrase, load_standard
from maaya.lexicon import connect, normalize


def _attester(standard):
    con = connect(":memory:")
    con.executemany("INSERT INTO phrases VALUES (?,?,?,?,?,?)", [("X1", "Bix a beel", normalize("Bix a beel"), "¿Cómo estás?", None, "C")])
    con.executemany("INSERT INTO words VALUES (?,?)", [("bix", 1), ("a", 1), ("beel", 1)])
    return Attester(con=con, standard=standard)


def test_levels_in_order():
    std = [StandardPhrase("STD0001", "Ma'alob k'iin", "Buenos días", "Good morning", "SRC", "")]
    a = _attester(std)
    assert a.check("Bix a beel").level == "exact"
    r = a.check("ma'alob k'iin!")
    assert r.level == "standard" and r.ok and r.ids == ["STD0001"]
    assert a.check("Bix a k'iin").level == "words"  # every word known via corpus or standard list
    assert a.check("Bix a tuunich").level == "partial"
    assert a.check("tuunich").level == "none"


def test_standard_list_is_well_formed():
    rows = load_standard()
    assert len(rows) >= 30
    ids = [r.id for r in rows]
    assert len(ids) == len(set(ids))
    assert all(r.id.startswith("STD") and r.yua and r.es and r.sources for r in rows)
    assert all("\u02bc" not in r.yua and "’" not in r.yua for r in rows), "INALI spelling uses the straight apostrophe"
