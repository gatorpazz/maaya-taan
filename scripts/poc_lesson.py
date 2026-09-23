"""Phase 0: a 3-minute proof-of-concept lesson (greeting exchange, backward
buildup, anticipation prompts) rendered to out/lessons/POC.mp3."""
from pathlib import Path

from maaya.render import Voices, render
from maaya.script import Script, response_pause
from maaya.tts.base import CachedTTS
from maaya.tts.kokoro import KokoroNarrator
from maaya.tts.mms import MMSMaya

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/tts"

s = Script(lesson_id="POC", title="Maaya T'aan – proof of concept")
s.narrator("This is Maaya T'aan, a proof of concept lesson. Listen to this short conversation between two neighbors meeting in the morning.")
s.maya("Bix a beel").pause(0.8).maya("Ma'alob").pause(1.5)
s.narrator("In the next few minutes you'll learn to say this yourself. The first speaker asked, how are you? Listen again.")
s.maya("Bix a beel").pause(1.0)
s.narrator("Bix a beel literally means, how is your road? We'll build it from the end. Listen and repeat the last word, beel.")
s.maya("beel", rate=0.8).pause(response_pause("beel"))
s.maya("beel", rate=0.8).pause(response_pause("beel"))
s.narrator("Now, a beel. Your road.")
s.maya("a beel", rate=0.8).pause(response_pause("a beel"))
s.narrator("And the whole question. Bix a beel.")
s.maya("Bix a beel", rate=0.8).pause(response_pause("Bix a beel"))
s.maya("Bix a beel").pause(response_pause("Bix a beel"))
s.narrator("The answer was, ma'alob. It means good, or fine. Notice the small catch in the middle of the word. That's a glottal stop, written with an apostrophe. Listen and repeat.")
s.maya("Ma'alob", rate=0.8).pause(response_pause("Ma'alob"))
s.maya("Ma'alob").pause(response_pause("Ma'alob"))
s.narrator("How do you say, fine?")
s.pause(2.5).maya("Ma'alob").pause(1.0)
s.narrator("Ask me, how are you?")
s.pause(3.0).maya("Bix a beel").pause(1.0)
s.narrator("Now imagine you meet your neighbor in the morning. Greet her.")
s.pause(3.0).maya("Bix a beel").pause(0.8)
s.narrator("She answers.")
s.maya("Ma'alob").pause(1.0)
s.narrator("Say, fine.")
s.pause(2.5).maya("Ma'alob").pause(1.0)
s.narrator("Listen to the conversation one more time. You can now follow both sides.")
s.maya("Bix a beel").pause(0.8).maya("Ma'alob").pause(1.5)
s.narrator("That's the end of the proof of concept.")

voices = Voices(narrator=CachedTTS(KokoroNarrator(), CACHE), maya=CachedTTS(MMSMaya(), CACHE))
out, _ = render(s, voices, ROOT / "out/lessons/POC.mp3", album="Maaya T'aan Level 0", track=0)
print("wrote", out)
